import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, make_response, request, send_from_directory
from flask_login import current_user

from app import db
from app.modules.hubfile import hubfile_bp
from app.modules.hubfile.models import HubfileDownloadRecord, HubfileViewRecord
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService

hubfile_bp = Blueprint("hubfile", __name__, url_prefix="/hubfile")


@hubfile_bp.route("/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    if not file.food_model or not file.food_model.dataset:
        return jsonify({"error": "File path not found (orphaned file)"}), 404

    user_id = file.food_model.dataset.user_id
    dataset_id = file.food_model.dataset.id

    directory_path = f"uploads/user_{user_id}/dataset_{dataset_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path)
    user_cookie = request.cookies.get("file_download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    existing_record = HubfileDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None, file_id=file_id, download_cookie=user_cookie
    ).first()

    if not existing_record:
        HubfileDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=file_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    resp = make_response(send_from_directory(directory=file_path, path=filename, as_attachment=True))
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@hubfile_bp.route("/view/<int:file_id>", methods=["GET"])
def view_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    if not file.food_model or not file.food_model.dataset:
        return jsonify({"success": False, "error": "File orphaned"}), 404

    user_id = file.food_model.dataset.user_id
    dataset_id = file.food_model.dataset.id

    directory_path = f"uploads/user_{user_id}/dataset_{dataset_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path, filename)

    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()

            user_cookie = request.cookies.get("view_cookie")
            if not user_cookie:
                user_cookie = str(uuid.uuid4())

            existing_record = HubfileViewRecord.query.filter_by(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                view_cookie=user_cookie,
            ).first()

            if not existing_record:
                new_view_record = HubfileViewRecord(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    file_id=file_id,
                    view_date=datetime.now(),
                    view_cookie=user_cookie,
                )
                db.session.add(new_view_record)
                db.session.commit()
            response = jsonify({"success": True, "content": content})

            if not request.cookies.get("view_cookie"):
                response = make_response(response)
                response.set_cookie("view_cookie", user_cookie, max_age=60 * 60 * 24 * 365 * 2)

            return response
        else:
            return jsonify({"success": False, "error": "File not found on disk"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
