import pytest
from datetime import datetime, timezone

from app import db
from app.modules.dataset.models import DataSet, DSMetaData, DSMetrics, PublicationType, Author
from app.modules.auth.models import User
from app.modules.recommendations.services import RecommendationService
from app.modules.recommendations.similarities import SimilarityService


@pytest.fixture
def user_with_datasets(test_client):
    """
    Crea un usuario con un dataset base y tres candidatos para testing de recomendaciones.
    """
    with test_client.application.app_context():
        user = User(email="rec@test.com", password="123")
        db.session.add(user)
        db.session.commit()

        # Dataset base
        base_metrics = DSMetrics(number_of_models=10, number_of_features=20)
        db.session.add(base_metrics)
        db.session.commit()

        base_meta = DSMetaData(
            title="Base Dataset",
            description="Base dataset description",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            tags="tag1,tag2",
            ds_metrics_id=base_metrics.id
        )
        db.session.add(base_meta)
        db.session.commit()

        Author(name="Author 1", ds_meta_data_id=base_meta.id)
        base_dataset = DataSet(
            user_id=user.id,
            ds_meta_data_id=base_meta.id,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(base_dataset)

        # Candidato 1: comparte autor y tipo publicación
        cand1_metrics = DSMetrics(number_of_models=5, number_of_features=5)
        db.session.add(cand1_metrics)
        db.session.commit()
        cand1_meta = DSMetaData(
            title="Candidate 1",
            description="Base dataset description",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            tags="tag1",
            ds_metrics_id=cand1_metrics.id
        )
        db.session.add(cand1_meta)
        db.session.commit()
        Author(name="Author 1", ds_meta_data_id=cand1_meta.id)
        cand1_dataset = DataSet(
            user_id=user.id,
            ds_meta_data_id=cand1_meta.id,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(cand1_dataset)

        # Candidato 2: distinto autor, distinto tipo publicación
        cand2_metrics = DSMetrics(number_of_models=0, number_of_features=0)
        db.session.add(cand2_metrics)
        db.session.commit()
        cand2_meta = DSMetaData(
            title="Candidate 2",
            description="Completely different description",
            publication_type=PublicationType.CONFERENCE_PAPER,
            tags="tag3",
            ds_metrics_id=cand2_metrics.id
        )
        db.session.add(cand2_meta)
        db.session.commit()
        Author(name="Author 2", ds_meta_data_id=cand2_meta.id)
        cand2_dataset = DataSet(
            user_id=user.id,
            ds_meta_data_id=cand2_meta.id,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(cand2_dataset)

        # Candidato 3: comparte autor pero distinto tipo publicación
        cand3_metrics = DSMetrics(number_of_models=3, number_of_features=7)
        db.session.add(cand3_metrics)
        db.session.commit()
        cand3_meta = DSMetaData(
            title="Candidate 3",
            description="Some overlapping description with base",
            publication_type=PublicationType.CONFERENCE_PAPER,
            tags="tag2,tag4",
            ds_metrics_id=cand3_metrics.id
        )
        db.session.add(cand3_meta)
        db.session.commit()
        Author(name="Author 1", ds_meta_data_id=cand3_meta.id)
        cand3_dataset = DataSet(
            user_id=user.id,
            ds_meta_data_id=cand3_meta.id,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(cand3_dataset)

        db.session.commit()

        yield user, base_dataset, [cand1_dataset, cand2_dataset, cand3_dataset]

        DataSet.query.filter_by(user_id=user.id).delete()
        DSMetaData.query.filter(DSMetaData.id.in_([base_meta.id, cand1_meta.id, cand2_meta.id, cand3_meta.id])).delete()
        DSMetrics.query.filter(DSMetrics.id.in_([base_metrics.id, cand1_metrics.id, cand2_metrics.id, cand3_metrics.id])).delete()
        Author.query.delete()
        User.query.filter_by(id=user.id).delete()
        db.session.commit()


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

        print(f"Candidato {i+1}: author={author_sim}, pub_type={pub_type_sim}, metric={metric}, text={text_sim:.3f}, final={final:.3f}")

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

    related = RecommendationService.get_related_datasets(base_ds, limit=5)

    # Verificamos que los datasets estén en el mismo orden que nuestro cálculo
    for i in range(min(len(expected_order), len(related))):
        assert related[i] == expected_order[i]

    assert len(related) > 0
    # Al menos el candidato más relevante debería estar en la lista
    assert candidates[0] in related
