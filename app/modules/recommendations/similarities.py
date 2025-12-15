from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimilarityService:

    def __init__(self, base_dataset, candidate_datasets):
        self.base = base_dataset
        self.candidates = candidate_datasets
        self._build_text_matrix()

    def _build_text_matrix(self):
        self.all_datasets = [self.base] + self.candidates

        text = []
        for ds in self.all_datasets:
            meta = ds.ds_meta_data

            title = getattr(meta, "title", "")
            description = getattr(meta, "description", "")
            tags = getattr(meta, "tags", "")

            text.append(f"{title} {description} {tags}")

        self.vectorizer = TfidfVectorizer(max_features=5000)

        self.tfidf_matrix = self.vectorizer.fit_transform(text)

    @staticmethod
    def author_similarity(ds1, ds2):
        authors1 = getattr(ds1.ds_meta_data, "authors", [])
        authors2 = getattr(ds2.ds_meta_data, "authors", [])

        author_list1 = {a.id for a in authors1}
        author_list2 = {a.id for a in authors2}

        return 1.0 if author_list1 & author_list2 else 0.0

    @staticmethod
    def publication_type_similarity(ds1, ds2):
        type_1 = ds1.ds_meta_data.publication_type
        type_2 = ds2.ds_meta_data.publication_type
        return 1.0 if type_1 == type_2 else 0.0

    def text_similarity(self, candidate_dataset_index):
        return cosine_similarity(self.tfidf_matrix[0], self.tfidf_matrix[candidate_dataset_index + 1])[0][0]

    @staticmethod
    def metric_score(candidate_dataset):
        metrics = candidate_dataset.ds_meta_data.ds_metrics
        if not metrics:
            return 0.0

        total_models = int(metrics.number_of_models or 0)
        total_features = int(metrics.number_of_features or 0)

        return min((total_models + total_features) / 100.0, 1.0)

    def final_score(self, candidate_ds_index):
        fixed_ds = self.base
        candidate_ds = self.candidates[candidate_ds_index]

        author_score = self.author_similarity(fixed_ds, candidate_ds)
        publication_type_score = self.publication_type_similarity(fixed_ds, candidate_ds)
        text_similarity_score = self.text_similarity(candidate_ds_index)
        metric_score = self.metric_score(candidate_ds)

        final_score = (
            0.2 * author_score + 0.15 * publication_type_score + 0.45 * text_similarity_score + 0.2 * metric_score
        )

        return final_score

    def recommendation(self, n_top_datasets=5):
        candidates_scores = []
        for index, candidate_dataset in enumerate(self.candidates):
            score = self.final_score(index)
            candidates_scores.append((candidate_dataset, score))

        candidates_scores.sort(key=lambda x: x[1], reverse=True)
        return candidates_scores[:n_top_datasets]
