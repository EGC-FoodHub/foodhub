from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.auth.services import AuthenticationService
from app.modules.profile import profile_bp
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.services import UserProfileService


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm()
    if request.method == "POST":
        service = UserProfileService()
        result, errors = service.update_profile(profile.id, form)
        return service.handle_service_response(
            result, errors, "profile.edit_profile", "Profile updated successfully", "profile/edit.html", form
        )

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/profile/summary")
@login_required
def my_profile():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    # IMPORTACIÓN DIFERIDA para evitar circular
    from app.modules.dataset.models import BaseDataset as DataSet

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == current_user.id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(DataSet).filter(DataSet.user_id == current_user.id).count()

    print(user_datasets_pagination.items)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )


# MANTÉN estas importaciones globales (no causan problemas circulares)
from core.resources.generic_resource import create_resource
from core.serialisers.serializer import Serializer


def init_blueprint_api(api):
    """Function to register resources with the provided Flask-RESTful Api instance."""
    # IMPORTACIÓN DIFERIDA dentro de la función para DataSet
    from app.modules.dataset.models import BaseDataset as DataSet
    
    file_fields = {"file_id": "id", "file_name": "name", "size": "get_formatted_size"}
    file_serializer = Serializer(file_fields)

    dataset_fields = {
        "dataset_id": "id",
        "created": "created_at",
        "name": "name",
        "doi": "get_uvlhub_doi",
        "files": "files",
    }

    dataset_serializer = Serializer(dataset_fields, related_serializers={"files": file_serializer})

    DataSetResource = create_resource(DataSet, dataset_serializer)
    
    api.add_resource(DataSetResource, "/api/v1/datasets/", endpoint="datasets")
    api.add_resource(DataSetResource, "/api/v1/datasets/<int:id>", endpoint="dataset")