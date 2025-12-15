from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from app.modules.basedataset.models import BaseDataset
from app.modules.profile import profile_bp
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.services import UserProfileService


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile()
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

    user_datasets_pagination = (
        db.session.query(BaseDataset)
        .filter(BaseDataset.user_id == current_user.id)
        .order_by(BaseDataset.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(BaseDataset).filter(BaseDataset.user_id == current_user.id).count()

    print(user_datasets_pagination.items)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )


@profile_bp.route("/profile/<int:user_id>")
def user_profile(user_id):

    user = User.query.get_or_404(user_id)
    page = request.args.get("page", 1, type=int)
    per_page = 5

    user_datasets_pagination = (
        db.session.query(BaseDataset)
        .filter(BaseDataset.user_id == user.id)
        .order_by(BaseDataset.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(BaseDataset).filter(BaseDataset.user_id == user.id).count()
    return render_template(
        "profile/summary.html",
        user_profile=user.profile,
        user=user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )


@profile_bp.route("/profile/metrics")
@login_required
def dashboard_metrics():
    profile = current_user.profile
    service = UserProfileService()
    metrics, errors = service.get_user_metrics(profile.user_id)

    if errors or not metrics:
        metrics = {
            "uploaded_datasets": 0,
            "downloads": 0,
            "synchronizations": 0,
        }

    return render_template("profile/dashboard.html", user_profile=profile, user=current_user, metrics=metrics)
