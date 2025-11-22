import logging

from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import current_user, login_required

from app.modules.fooddataset.repositories import FoodDatasetRepository
from app.modules.fooddataset.services import FoodDatasetService

logger = logging.getLogger(__name__)

food_bp = Blueprint("food_dataset", __name__, url_prefix="/food")

food_service = FoodDatasetService()
food_repo = FoodDatasetRepository()


# ============================================================
#  CREATE FOOD DATASET (simple)
# ============================================================
@food_bp.route("/create", methods=["POST"])
@login_required
def create_food_dataset():
    """
    Crea un dataset Food vacío (sin archivos).
    El proceso completo se hace desde la UI genérica.
    """
    name = request.json.get("name")

    if not name:
        return jsonify({"error": "Name is required"}), 400

    dataset = food_service.create_food_dataset(current_user, name)

    return jsonify({"message": "FoodDataset created", "dataset_id": dataset.id}), 200


# ============================================================
#  UPLOAD & PARSE FOOD FILE (.food)
# ============================================================
@food_bp.route("/<int:dataset_id>/upload-food", methods=["POST"])
@login_required
def upload_food_file(dataset_id):

    dataset = food_repo.get_or_404(dataset_id)

    if dataset.owner_user_id != current_user.id:
        abort(403)

    file = request.files.get("file")

    if not file:
        return jsonify({"error": "File is required"}), 400

    if not file.filename.endswith(".food"):
        return jsonify({"error": "Only .food files are allowed"}), 400

    try:
        hubfile = food_service.parse_uploaded_file(dataset, file)

    except Exception as exc:
        logger.exception(exc)
        return jsonify({"error": str(exc)}), 400

    return jsonify({"message": "Food file uploaded and parsed", "file_id": hubfile.id}), 200


# ============================================================
#  VIEW METADATA AND NUTRITION
# ============================================================
@food_bp.route("/<int:dataset_id>")
def view_food_dataset(dataset_id):

    dataset = food_repo.get_or_404(dataset_id)

    return render_template(
        "food/view_food_dataset.html",
        dataset=dataset,
        metadata=dataset.metadata,
        nutritional_values=dataset.metadata.nutritional_values if dataset.metadata else None,
        files=dataset.files,
    )


# ============================================================
#  GET NUTRITIONAL VALUES (AJAX)
# ============================================================
@food_bp.route("/<int:dataset_id>/nutrition")
def get_nutritional_values(dataset_id):
    nv = food_service.get_nutritional_values(dataset_id)

    if not nv:
        return jsonify({"error": "No nutritional values found"}), 404

    return jsonify(
        {
            "protein": nv.protein,
            "carbohydrates": nv.carbohydrates,
            "fat": nv.fat,
            "fiber": nv.fiber,
            "vitamin_e": nv.vitamin_e,
            "magnesium": nv.magnesium,
            "calcium": nv.calcium,
        }
    )


# ============================================================
#  LIST FOOD FILES
# ============================================================
@food_bp.route("/<int:dataset_id>/files")
def list_food_files(dataset_id):
    files = food_service.get_files(dataset_id)
    return jsonify(
        [
            {
                "id": f.id,
                "name": f.name,
                "size": f.size,
                "checksum": f.checksum,
            }
            for f in files
        ]
    )


# ============================================================
#  DELETE FOOD DATASET
# ============================================================
@food_bp.route("/<int:dataset_id>/delete", methods=["DELETE"])
@login_required
def delete_food_dataset(dataset_id):

    dataset = food_repo.get_or_404(dataset_id)

    if dataset.owner_user_id != current_user.id:
        abort(403)

    ok = food_service.delete_dataset(dataset_id)

    return jsonify({"deleted": ok}), 200
