from sklearn.feature_extraction.text import TfidfVectorizer
from app.modules.dataset.repositories import DataSetRepository

class SimilarityService:
    
    def __init__(self, base_dataset, candidate_datasets):
        self.base = base_dataset
        self.candidates = candidate_datasets
        self._build_text_matrix()
    
    def _build_text_matrix(self):
        self.all_datasets = [self.base] + self.candidates
        text = [f"{ds.title} {ds.description} {ds.tags or ""}" for ds in self.all_datasets]
        self.vectorizer = TfidfVectorizer(
            stop_words="spanish",
            max_features=5000
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(text)

    @staticmethod
    def author_similarity(ds1, ds2):
        author_list1 = {a.id for a in ds1.authors}
        author_list2 = {a.id for a in ds2.authors}
        return 1.0 if len(author_list1 & author_list2) > 0 else 0.0
    
    @staticmethod
    def publication_type_similarity(ds1, ds2):
        type_1 = ds1.publication_type
        type_2 = ds2.publication_type
        return 1.0 if type_1 == type_2 else 0.0
    
    @staticmethod
    def text_similarity(self, candidate_dataset_index):
        return cosine_similarity(self.tfidf_matrix[0],
                                 self.tfidf_matrix[candidate_dataset_index + 1])[0][0]
    
    @staticmethod
    def metric_score(candidate_dataset):
        if not candidate_dataset.ds_metrics:
            return 0.0
        
        total_downloads = getattr(candidate_dataset.ds_metrics, "downloads", 0)
        total_citations = getattr(candidate_dataset.ds_metrics, "citations", 0)
        
        return min((total_downloads + total_citations)/100.0 , 1.0)
    
    def final_score(self, candidate_ds_index):
        fixed_ds = self.base
        candidate_ds = self.candidates[candidate_ds_index]

        author_score = self.author_similarity(fixed_ds, candidate_ds)
        publication_type_score = self.publication_type_similarity(fixed_ds, candidate_ds)
        text_similarity_score = self.text_similarity(candidate_ds_index)
        metric_score = self.metric_score(candidate_ds)

        final_score = (
            0.5 * author_score +
            0.4 * publication_type_score +
            0.8 * text_similarity_score +
            0.2 * metric_score
        )

        return final_score

    def recommendation(self, n_top_datasets = 5):
        candidates_scores = []
        for index, candidate_dataset in enumerate(self.candidates):
            score = self.final_score(index)
            candidates_scores.append((candidate_dataset, score))
            
        candidates_scores.sort(key = lambda x: x[1], reverse=True)
        return candidates_scores[:n_top_datasets]