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
    
    def final_score(self, candidate_ds_index):
        fixed_ds = self.base
        candidate_ds = self.candidates[candidate_ds_index]

        author_score = self.author_similarity(fixed_ds, candidate_ds)
        publication_type_score = self.publication_type_similarity(fixed_ds, candidate_ds)

        final_score = (
            0.5 * author_score +
            0.4 * publication_type_score
        )

        return final_score
