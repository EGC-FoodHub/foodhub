import pytest
from datetime import datetime, timezone

from app import db
from app.modules.basedataset.models import BaseDataset, BaseAuthor, BaseDSMetrics, BasePublicationType, BaseDSMetaData
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData
from app.modules.auth.models import User
from app.modules.recommendations.services import RecommendationService
from app.modules.recommendations.similarities import SimilarityService
import uuid


@pytest.fixture
def user_with_datasets(test_client):
    """
    Crea un usuario con un dataset base y tres candidatos para testing de recomendaciones.
    """
    with test_client.application.app_context():
        email = f"rec_{uuid.uuid4().hex}@test.com"
        user = User(email=email, password="123")

        db.session.add(user)
        db.session.commit()

        # Dataset base
        base_metrics = BaseDSMetrics(number_of_models=10, number_of_features=5)

        db.session.add(base_metrics)
        db.session.commit()

        base_meta = FoodDSMetaData(
            title="Base Dataset",
            description="Base dataset description",
            publication_type=BasePublicationType.JOURNAL_ARTICLE,
            tags="tag1,tag2",
            ds_metrics_id=base_metrics.id
        )

        db.session.add(base_meta)
        db.session.commit()

        author = BaseAuthor(name="Author 1", food_ds_meta_data_id=base_meta.id)
        db.session.add(author)
        db.session.commit()

        base_dataset = FoodDataset(
            user_id=user.id,
            ds_meta_data_id=base_meta.id,
            created_at=datetime.now(timezone.utc)
        )

        db.session.add(base_dataset)
        db.session.flush()

        # Candidato 1: comparte autor y tipo publicación
        cand1_metrics = BaseDSMetrics(number_of_models=5, number_of_features=3)

        db.session.add(cand1_metrics)
        db.session.commit()

        cand1_meta = FoodDSMetaData(
            title="Candidate 1",
            description="Base dataset description",
            publication_type=BasePublicationType.JOURNAL_ARTICLE,
            tags="tag1",
            ds_metrics_id=cand1_metrics.id
        )

        db.session.add(cand1_meta)
        db.session.commit()

        author1 = BaseAuthor(name="Author 1", food_ds_meta_data_id=cand1_meta.id)
        db.session.add(author1)
        db.session.commit()

        cand1_dataset = FoodDataset(
            user_id=user.id,
            ds_meta_data_id=cand1_meta.id,
            created_at=datetime.now(timezone.utc)
        )

        db.session.add(cand1_dataset)
        db.session.flush()

        # Candidato 2: distinto autor, distinto tipo publicación
        cand2_metrics = BaseDSMetrics(number_of_models=0, number_of_features=0)

        db.session.add(cand2_metrics)
        db.session.commit()

        cand2_meta = FoodDSMetaData(
            title="Candidate 2",
            description="Completely different description",
            publication_type=BasePublicationType.CONFERENCE_PAPER,
            tags="tag3",
            ds_metrics_id=cand2_metrics.id
        )

        db.session.add(cand2_meta)
        db.session.commit()

        author2 = BaseAuthor(name="Author 2", food_ds_meta_data_id=cand2_meta.id)
        db.session.add(author2)
        db.session.commit()

        cand2_dataset = FoodDataset(
            user_id=user.id,
            ds_meta_data_id=cand2_meta.id,
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(cand2_dataset)
        db.session.flush()

        # Candidato 3: comparte autor pero distinto tipo publicación
        cand3_metrics = BaseDSMetrics(number_of_models=3, number_of_features=2)

        db.session.add(cand3_metrics)
        db.session.commit()

        cand3_meta = FoodDSMetaData(
            title="Candidate 3",
            description="Some overlapping description with base",
            publication_type=BasePublicationType.CONFERENCE_PAPER,
            tags="tag2,tag4",
            ds_metrics_id=cand3_metrics.id
        )

        db.session.add(cand3_meta)
        db.session.commit()

        author3 = BaseAuthor(name="Author 1", food_ds_meta_data_id=cand3_meta.id)
        db.session.add(author3)
        db.session.commit()

        cand3_dataset = FoodDataset(
            user_id=user.id,
            ds_meta_data_id=cand3_meta.id,
            created_at=datetime.now(timezone.utc)
        )

        db.session.add(cand3_dataset)
        db.session.flush()

        db.session.commit()

        yield user, base_dataset, [cand1_dataset, cand2_dataset, cand3_dataset]

        db.session.rollback()


# ---------------------------
# Test SimilarityService
# ---------------------------

def test_similarity_service_completo(user_with_datasets):
    _, base_ds, candidates = user_with_datasets
    service = SimilarityService(base_ds, candidates)

    for i, cand in enumerate(candidates):
        author_sim = service.author_similarity(base_ds, cand)
        pub_type_sim = service.publication_type_similarity(base_ds, cand)
        metric = service.metric_score(cand)
        text_sim = service.text_similarity(i)
        final = service.final_score(i)


        assert 0 <= author_sim <= 1
        assert 0 <= pub_type_sim <= 1
        assert 0 <= metric <= 1
        assert 0 <= text_sim <= 1
        assert 0 <= final <= 1

    recs = service.recommendation(n_top_datasets=3)
    assert len(recs) == 3
    # El más similar (cand1) debería estar primero
    assert recs[0][0] == candidates[0]

# ---------------------------
# Test RecommendationService
# ---------------------------

def test_recommendation_service(user_with_datasets):
    _, base_ds, candidates = user_with_datasets

    service = SimilarityService(base_ds, candidates)

    expected_order = [ds for ds, score in service.recommendation(n_top_datasets=len(candidates))]

    related = RecommendationService.get_related_food_datasets(base_ds, limit=5)

    # Verificamos que los datasets estén en el mismo orden que nuestro cálculo
    for i in range(min(len(expected_order), len(related))):
        assert related[i].id == expected_order[i].id

    assert len(related) > 0
    # Al menos el candidato más relevante debería estar en la lista
    assert candidates[0] in related
