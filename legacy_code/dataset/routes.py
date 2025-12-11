import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile

from flask import abort, jsonify, make_response, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

import app
from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import AuthorForm, DataSetForm
from app.modules.dataset.models import DSDownloadRecord
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
from app.modules.fakenodo.services import FakenodoService
from app.modules.recommendations.services import RecommendationService


logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
fakenodo_service = FakenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Fakenodo
        data = {}
        try:
            fakenodo_response_json = fakenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(fakenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            fakenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Fakenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Fakenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each feature model (one feature model = one request to Fakenodo)
                for feature_model in dataset.feature_models:
                    fakenodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                fakenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = fakenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in Fakenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/save_as_draft", methods=["GET", "POST"])
@login_required
def create_dataset_as_draft():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        form.title.data = form.title.data if form.title.data else ""
        form.desc.data = form.desc.data if form.desc.data else ""
        form.feature_models.entries = []

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/edit/<int:dataset_id>", methods=["GET", "POST"])
@login_required
def edit_doi_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    # form = DataSetForm(obj=dataset.ds_meta_data)
    form = DataSetForm()

    if request.method == "POST":
        result, errors = dataset_service.edit_doi_dataset(dataset, form)
        return dataset_service.handle_service_response(
            result, errors, "dataset.list_dataset", "Dataset updated", "dataset/edit_dataset.html", form
        )
    else:
        form.title.data = dataset.ds_meta_data.title
        form.desc.data = dataset.ds_meta_data.description
        form.publication_type.data = dataset.ds_meta_data.publication_type.value
        form.publication_doi.data = dataset.ds_meta_data.publication_doi
        form.tags.data = dataset.ds_meta_data.tags
        form.desc.data = dataset.ds_meta_data.description

        form.authors.entries = []
        for author in dataset.ds_meta_data.authors:
            subform = AuthorForm()
            subform.name.data = author.name
            subform.affiliation.data = author.affiliation
            subform.orcid.data = author.orcid
            form.authors.append_entry(subform.data)

    return render_template("dataset/edit_dataset.html", form=form, dataset=dataset)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"message": "No file provided"}), 400

    filename = file.filename.lower()
    allowed_extensions = [".uvl", ".food"]

    # Validación de extensión
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return jsonify({"message": "File type not allowed"}), 400

    temp_folder = current_user.temp_folder()

    # Crear carpeta temporal si no existe
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # Generar ruta final
    file_path = os.path.join(temp_folder, file.filename)

    # Evitar sobreescritura: generar nombre único si ya existe
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

    # Mensaje de confirmación según tipo
    file_type = "UVL" if filename.endswith(".uvl") else "Food" if filename.endswith(".food") else "Unknown"

    return (
        jsonify(
            {
                "message": f"{file_type} file uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Check if the download record already exists for this cookie
    existing_record = DSDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie,
    ).first()

    if not existing_record:
        # Record the download in your database
        DSDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

        logger.info("Created new DSDownloadRecord for dataset=%s cookie=%s", dataset_id, user_cookie)

        # If the user is authenticated, increment their downloaded datasets counter
        try:
            if current_user.is_authenticated and getattr(current_user, "profile", None):
                profile = current_user.profile
                profile.downloaded_datasets_count = (profile.downloaded_datasets_count or 0) + 1
                profile.save()
                logger.info(
                    "Incremented downloaded_datasets_count for user_id=%s to %s",
                    current_user.id,
                    profile.downloaded_datasets_count,
                )
        except SQLAlchemyError:
            logger.exception("Failed to update user's downloaded_datasets_count")
    else:
        logger.info(
            "Existing DSDownloadRecord found for dataset=%s cookie=%s user_id=%s",
            dataset_id,
            user_cookie,
            existing_record.user_id,
        )
        # If record exists but was anonymous and user is authenticated, attach it to the user and increment
        try:
            if (
                current_user.is_authenticated
                and existing_record.user_id is None
                and getattr(current_user, "profile", None)
            ):
                existing_record.user_id = current_user.id
                app.db.session.commit()
                profile = current_user.profile
                profile.downloaded_datasets_count = (profile.downloaded_datasets_count or 0) + 1
                profile.save()
                logger.info(
                    "Attached anonymous DSDownloadRecord to user_id=%s and incremented counter to %s",
                    current_user.id,
                    profile.downloaded_datasets_count,
                )
        except SQLAlchemyError:
            logger.exception("Failed while attaching anonymous download record or updating counter")

    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    related_datasets = RecommendationService.get_related_datasets(dataset, limit=5)

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset, related_datasets=related_datasets))
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)
        
    related_datasets = RecommendationService.get_related_datasets(dataset, limit=5)

    return render_template("dataset/view_dataset.html", dataset=dataset, related_datasets=related_datasets)
