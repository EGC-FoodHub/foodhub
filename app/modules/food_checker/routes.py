from flask import render_template
from app.modules.food_checker import food_checker_bp

import os
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.modules.food_checker.services import FoodCheckerService
from app.modules.basedataset.services import BaseDatasetService

food_checker_bp = Blueprint('food_checker', __name__, url_prefix='/api/food_checker')
checker_service = FoodCheckerService()
dataset_service = BaseDatasetService()

@food_checker_bp.route('/check/temp', methods=['POST'])
@login_required
def check_temp_file():
    """Valida archivo antes de subir (Dropzone)."""
    data = request.get_json()
    filename = data.get('filename')
    path = os.path.join(current_user.temp_folder(), filename)
    return jsonify(checker_service.check_file_path(path))

@food_checker_bp.route('/check/file/<int:file_id>', methods=['GET'])
def check_file(file_id):
    """Muestra datos de un archivo subido."""
    return jsonify(checker_service.check_hubfile(file_id))

@food_checker_bp.route('/check/dataset/<int:dataset_id>', methods=['GET'])
def check_dataset(dataset_id):
    """Analiza todo el dataset."""
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    return jsonify(checker_service.check_dataset(dataset))
