import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile

from flask import (
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app.modules.basedataset import basedataset_bp
from app.modules.basedataset.forms import BaseDatasetForm
from app.modules.basedataset.services import BaseDatasetService
from app.modules.basedataset.services import (
    AuthorService,
    DOIMappingService,
    BDSMetaDataService,
    BDSViewRecordService,
    BDSDownloadRecordService,
)
from app.modules.basedataset.factory import DatasetFactory
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)

# Servicios centrales (genéricos)
dataset_service = BaseDatasetService()
author_service = AuthorService()
metadata_service = BDSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
view_record_service = BDSViewRecordService()
download_record_service = BDSDownloadRecordService()


# ============================================================
#  CREATE DATASET (GENERIC)
# ============================================================
@basedataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = BaseDatasetForm()

    if request.method == "POST":

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        # Detect dataset type (UVL, FOOD, XML, YAML…)
        dataset_type = form.dataset_type.data

        # Get correct service
        dataset_specific_service = DatasetFactory.get_service(dataset_type)

        try:
            # 1. Create dataset + metadata + authors using specific service
            dataset = dataset_specific_service.create_from_form(form=form, current_user=current_user)

            # 2. Move uploaded files to final folder
            dataset_specific_service.move_dataset_files(dataset)

        except Exception as exc:
            logger.exception(f"Exception creating dataset: {exc}")
            return jsonify({"error": str(exc)}), 400

        # ---------- ZENODO INTEGRATION ----------
        try:
            zenodo_data = zenodo_service.create_new_deposition(dataset)
            deposition_id = zenodo_data.get("id")

            if deposition_id:
                metadata_service.update(dataset.meta_data_id, deposition_id=deposition_id)

                # Upload each file belonging to dataset
                for file in dataset.files:
                    zenodo_service.upload_file(dataset, deposition_id, file)

                # Publish in Zenodo
                zenodo_service.publish_deposition(deposition_id)

                # Update DOI in metadata
                new_doi = zenodo_service.get_doi(deposition_id)
                metadata_service.update(dataset.meta_data_id, dataset_doi=new_doi)

        except Exception as exc:
            logger.exception(f"Zenodo error: {exc}")

        # Clean temporary folder
        temp = current_user.temp_folder()
        if os.path.exists(temp):
            shutil.rmtree(temp)

        return jsonify({"message": "Dataset created successfully"}), 200

    return render_template("dataset/upload_dataset.html", form=form)


# ============================================================
#  LIST
# ============================================================
@basedataset_bp.route("/dataset/list")
@login_required
def list_datasets():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


# ============================================================
#  UPLOAD FILE (GENERIC)
# ============================================================
@basedataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload_file():
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file provided"}), 400

    allowed_extensions = DatasetFactory.allowed_extensions()

    filename = file.filename.lower()

    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return jsonify({"message": "File type not allowed"}), 400

    temp_folder = current_user.temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        base, ext = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(os.path.join(temp_folder, f"{base} ({i}){ext}")):
            i += 1
        file_path = os.path.join(temp_folder, f"{base} ({i}){ext}")

    file.save(file_path)

    return jsonify({"message": "File uploaded", "filename": os.path.basename(file_path)}), 200


# ============================================================
#  DELETE TEMP FILE
# ============================================================
@basedataset_bp.route("/dataset/file/delete", methods=["POST"])
@login_required
def delete_file():
    data = request.get_json()
    filename = data.get("file")
    path = os.path.join(current_user.temp_folder(), filename)

    if os.path.exists(path):
        os.remove(path)
        return jsonify({"message": "File deleted"})

    return jsonify({"error": "File not found"})


# ============================================================
#  DOWNLOAD ZIP
# ============================================================
@basedataset_bp.route("/dataset/download/<int:dataset_id>")
def download_dataset(dataset_id):

    dataset = dataset_service.get_or_404(dataset_id)

    dataset_folder = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for root, dirs, files in os.walk(dataset_folder):
            for file in files:
                full = os.path.join(root, file)
                arc = os.path.relpath(full, dataset_folder)
                zipf.write(full, arcname=arc)

    # Cookie to prevent multiple counts
    cookie = request.cookies.get("download_cookie") or str(uuid.uuid4())

    response = make_response(
        send_from_directory(temp_dir, f"dataset_{dataset_id}.zip", as_attachment=True)
    )
    response.set_cookie("download_cookie", cookie)

    # Record download
    existing = download_record_service.record_exists(dataset, cookie)
    if not existing:
        download_record_service.create_new(dataset, cookie)

    return response


# ============================================================
#  DOI RESOLUTION
# ============================================================
@basedataset_bp.route("/doi/<path:doi>")
def view_dataset_by_doi(doi):

    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(url_for("dataset.view_dataset_by_doi", doi=new_doi), code=302)

    metadata = metadata_service.filter_by_doi(doi)
    if not metadata:
        abort(404)

    dataset = metadata.dataset

    cookie = view_record_service.create_cookie(dataset)

    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    resp.set_cookie("view_cookie", cookie)

    return resp


# ============================================================
#  GET UNSYNCHRONIZED
# ============================================================
@basedataset_bp.route("/dataset/unsynchronized/<int:dataset_id>")
@login_required
def get_unsynchronized_dataset(dataset_id):

    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    return render_template("dataset/view_dataset.html", dataset=dataset)
