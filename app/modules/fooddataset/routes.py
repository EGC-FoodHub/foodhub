import json
import logging
import os
import shutil

from flask import Blueprint, jsonify, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from app.modules.fooddataset.forms import FoodDatasetForm
from app.modules.fooddataset.services import FoodDatasetService
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)

fooddataset_bp = Blueprint("fooddataset", __name__, template_folder="templates", static_folder="assets")

food_service = FoodDatasetService()


@fooddataset_bp.route("/scripts.js")
def scripts():
    return send_from_directory(os.path.join(os.path.dirname(__file__), "assets"), "scripts.js")


@fooddataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = FoodDatasetForm()

    if request.method == "POST":
        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": str(form.errors)}), 400

        try:
            logger.info("Creating food dataset...")
            dataset = food_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset.id}")

        except Exception as exc:
            logger.exception(f"Exception creating local dataset: {exc}")
            return jsonify({"message": str(exc)}), 400

        zenodo_service = ZenodoService()

        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            logger.exception(f"Exception creating Zenodo deposition: {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            try:
                for food_model in dataset.files:
                    zenodo_service.upload_file(dataset, deposition_id, food_model)

                zenodo_service.publish_deposition(deposition_id)

                zenodo_service.get_doi(deposition_id)

            except Exception as e:
                msg = f"Error uploading to Zenodo: {e}"
                logger.error(msg)
                return jsonify({"message": msg}), 200

        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Dataset created successfully!"
        return jsonify({"message": msg, "redirect": url_for("basedataset.list_dataset")}), 200

    return render_template("fooddataset/upload_dataset.html", form=form)


@fooddataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload_file_temp():
    file = request.files.get("file")
    if not file:
        return jsonify({"message": "No file provided"}), 400

    filename = file.filename.lower()

    allowed_extensions = [".food"]

    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return jsonify({"message": "File type not allowed (only .food)"}), 400

    temp_folder = current_user.temp_folder()

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){extension}")):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return jsonify({"message": "File uploaded successfully", "filename": new_filename}), 200


@fooddataset_bp.route("/dataset/file/delete", methods=["POST"])
@login_required
def delete_file_temp():
    data = request.get_json()
    filename = data.get("file")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "File not found"})