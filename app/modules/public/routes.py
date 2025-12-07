import logging

from flask import render_template

# Usamos el servicio de FoodDataset (que hereda de BaseDataset)
from app.modules.fooddataset.services import FoodDatasetService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")

    # Usamos FoodDatasetService para obtener datos reales
    dataset_service = FoodDatasetService()

    # Statistics: total datasets (synchronized)
    datasets_counter = dataset_service.count_synchronized_datasets()

    # Statistics: total downloads & views (Genérico para el dataset)
    total_dataset_downloads = dataset_service.total_dataset_downloads()
    total_dataset_views = dataset_service.total_dataset_views()

    # ELIMINADO: Contadores de FeatureModel (ya no aplican)

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        datasets_counter=datasets_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_dataset_views=total_dataset_views,
        # Si la plantilla HTML espera estas variables, pásalas como 0 para no romper el frontend
        feature_models_counter=0,
        total_feature_model_downloads=0,
        total_feature_model_views=0,
    )
