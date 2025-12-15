import logging

from flask import render_template

from app.modules.fooddataset.services import FoodDatasetService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")

    dataset_service = FoodDatasetService()

    datasets_counter = dataset_service.count_synchronized_datasets()
    total_dataset_downloads = dataset_service.total_dataset_downloads()
    total_dataset_views = dataset_service.total_dataset_views()
    food_models_counter = dataset_service.count_food_models()
    total_food_model_downloads = dataset_service.total_food_model_downloads()
    total_food_model_views = dataset_service.total_food_model_views()

    trending_weekly = dataset_service.get_trending_weekly(limit=3)

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        datasets_counter=datasets_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_dataset_views=total_dataset_views,
        food_models_counter=food_models_counter,
        total_food_model_downloads=total_food_model_downloads,
        total_food_model_views=total_food_model_views,
        trending_weekly=trending_weekly,
    )
