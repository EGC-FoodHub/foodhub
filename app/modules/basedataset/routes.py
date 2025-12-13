import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile
from app.modules.recommendations.services import RecommendationService

from flask import (
    Blueprint,
    abort,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.modules.basedataset.services import (
    BaseDatasetService,
    BaseDOIMappingService,
    BaseDSDownloadRecordService,
    BaseDSMetaDataService,
    BaseDSViewRecordService,
)

logger = logging.getLogger(__name__)

basedataset_bp = Blueprint("basedataset", __name__, template_folder="templates")

dataset_service = BaseDatasetService()
dsmetadata_service = BaseDSMetaDataService()
doi_mapping_service = BaseDOIMappingService()
ds_view_record_service = BaseDSViewRecordService()
ds_download_record_service = BaseDSDownloadRecordService()


@basedataset_bp.route("/dataset/list", methods=["GET"])
@login_required
def list_dataset():
    """
    Lista todos los datasets del usuario (Food, etc.)
    """
    from app.modules.fooddataset.services import FoodDatasetService

    food_service = FoodDatasetService()

    return render_template(
        "basedataset/list_datasets.html",
        datasets=food_service.get_synchronized(current_user.id),
        local_datasets=food_service.get_unsynchronized(current_user.id),
    )


@basedataset_bp.route("/dataset/<int:dataset_id>", methods=["GET"])
@login_required
def view_dataset(dataset_id):
    """
    Vista de detalle para un dataset específico (acceso por ID).
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        abort(404)

    return render_template("basedataset/view_dataset.html", dataset=dataset)


@basedataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        abort(404)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    if not os.path.exists(file_path):
        abort(404, description="Dataset files not found on server")

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

    existing_record = ds_download_record_service.repository.model.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie,
    ).first()

    if not existing_record:
        ds_download_record_service.create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    return resp


@basedataset_bp.route("/dataset/download", methods=["GET"])
def download_datasets():
    ids_str = request.args.get("ids")
    if not ids_str:
        abort(400, description="No dataset IDs provided")

    try:
        dataset_ids = [int(i) for i in ids_str.split(",")]
    except ValueError:
        abort(400, description="Invalid dataset IDs")

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"datasets_{'_'.join(map(str, dataset_ids))}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for dataset_id in dataset_ids:
            dataset = dataset_service.get_by_id(dataset_id)
            if not dataset:
                continue

            file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"
            if not os.path.exists(file_path):
                continue

            for subdir, dirs, files in os.walk(file_path):
                for file in files:
                    full_path = os.path.join(subdir, file)
                    relative_path = os.path.relpath(full_path, file_path)
                    zipf.write(
                        full_path,
                        arcname=os.path.join(f"dataset_{dataset.id}", relative_path),
                    )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())
        resp = make_response(
            send_from_directory(
                temp_dir,
                os.path.basename(zip_path),
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            os.path.basename(zip_path),
            as_attachment=True,
            mimetype="application/zip",
        )

    for dataset_id in dataset_ids:
        existing_record = ds_download_record_service.repository.model.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_cookie=user_cookie,
        ).first()

        if not existing_record:
            ds_download_record_service.create(
                user_id=current_user.id if current_user.is_authenticated else None,
                dataset_id=dataset_id,
                download_date=datetime.now(timezone.utc),
                download_cookie=user_cookie,
            )

    return resp


@basedataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(url_for("basedataset.subdomain_index", doi=new_doi), code=302)

    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Try to find the dataset via FoodDSMetaData (subclass) since BaseDSMetaData doesn't have the relationship
    # We must expunge the base object from session to avoid Identity Map collision preventing the subclass load
    db.session.expunge(ds_meta_data)

    from app.modules.fooddataset.models import FoodDSMetaData

    food_meta_data = FoodDSMetaData.query.get(ds_meta_data.id)

    dataset = food_meta_data.dataset if food_meta_data else None

    if not dataset:
        abort(404)

    related_datasets = RecommendationService.get_related_food_datasets(dataset, limit=5)

    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)

    resp = make_response(render_template("basedataset/view_dataset.html", dataset=dataset, related_datasets=related_datasets))
    resp.set_cookie("view_cookie", user_cookie)

    return resp
