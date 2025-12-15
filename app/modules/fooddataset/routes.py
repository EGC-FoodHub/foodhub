import json
import logging
import os
import shutil
import tempfile
import urllib.error
import urllib.request
from zipfile import ZipFile

from flask import Blueprint, jsonify, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from app.modules.basedataset.repositories import BaseDOIMappingRepository
from app.modules.basedataset.services import BaseDSMetaDataService
from app.modules.fakenodo.services import FakenodoService
from app.modules.fooddataset.forms import AuthorForm, FoodDatasetForm, FoodModelForm
from app.modules.fooddataset.services import FoodDatasetService
from core.services.SearchService import SearchService

logger = logging.getLogger(__name__)

fooddataset_bp = Blueprint("fooddataset", __name__, template_folder="templates", static_folder="assets")

food_service = FoodDatasetService()
search_service = SearchService()
base_doi_mapping_repository = BaseDOIMappingRepository()
dsmetadata_service = BaseDSMetaDataService()


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

            try:
                search_service.index_dataset(dataset)
            except Exception as e:
                logger.error(f"Failed to index dataset in Elasticsearch: {e}")

        except Exception as exc:
            logger.exception(f"Exception creating local dataset: {exc}")
            return jsonify({"message": str(exc)}), 400

        fakenodo_service = FakenodoService()

        data = {}
        try:
            fakenodo_response_json = fakenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(fakenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            logger.exception(f"Exception creating Fakenodo deposition: {exc}")

        if data.get("doi"):
            deposition_id = data.get("id")

            try:
                for food_model in dataset.files:
                    fakenodo_service.upload_file(dataset, deposition_id, food_model)

                fakenodo_service.publish_deposition(deposition_id)
                doi = fakenodo_service.get_doi(deposition_id)
                base_doi_mapping_repository.create(dataset.ds_meta_data_id, dataset_doi_old=doi)
                dsmetadata_service.update(dataset.ds_meta_data_id, dataset_doi=doi)

            except Exception as e:
                msg = f"Error uploading to Fakenodo: {e}"
                logger.error(msg)
                return jsonify({"message": msg}), 400

        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Dataset created successfully!"
        return jsonify({"message": msg, "redirect": url_for("basedataset.list_dataset")}), 200

    return render_template("fooddataset/upload_dataset.html", form=form)


@fooddataset_bp.route("/dataset/save_as_draft", methods=["GET", "POST"])
@login_required
def create_dataset_as_draft():
    form = FoodDatasetForm()
    if request.method == "POST":

        dataset = None

        if not form.food_models.entries[0].filename.data:
            form.food_models = []

        try:
            logger.info("Creating dataset...")
            dataset = food_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("fooddataset/upload_dataset.html", form=form)


@fooddataset_bp.route("/dataset/publish/<int:dataset_id>", methods=["GET", "POST"])
@login_required
def upload_draft_dataset(dataset_id):
    dataset = food_service.get_or_404(dataset_id)
    form = FoodDatasetForm()

    temp_folder = current_user.temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    working_dir = os.getenv("WORKING_DIR", "")
    dataset_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")

    for food_model in dataset.files:
        for file in food_model.files:
            src_file = os.path.join(dataset_dir, file.name)
            dest_file = os.path.join(temp_folder, file.name)

            if not os.path.exists(src_file):
                continue

            if os.path.exists(dest_file):
                base_name, ext = os.path.splitext(file.name)
                i = 1
                while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){ext}")):
                    i += 1
                dest_file = os.path.join(temp_folder, f"{base_name} ({i}){ext}")

            shutil.copy(src_file, dest_file)

    result, errors = food_service.edit_doi_dataset(dataset, form)
    fakenodo_service = FakenodoService()
    dataset = food_service.get_or_404(dataset_id)

    os.makedirs(dataset_dir, exist_ok=True)

    for food_model in dataset.files:
        food_filename = food_model.food_meta_data.food_filename
        src = os.path.join(temp_folder, food_filename)
        dst = os.path.join(dataset_dir, food_filename)

        if not os.path.exists(dst):
            if not os.path.exists(src):
                raise FileNotFoundError(f"Missing file for upload: {food_filename}")
            shutil.copy(src, dst)

    data = {}
    try:
        fakenodo_response_json = fakenodo_service.create_new_deposition(dataset)
        response_data = json.dumps(fakenodo_response_json)
        data = json.loads(response_data)
    except Exception as exc:
        logger.exception(f"Exception creating Fakenodo deposition: {exc}")

    if data.get("doi"):
        deposition_id = data.get("id")

        try:
            for food_model in dataset.files:
                fakenodo_service.upload_file(dataset, deposition_id, food_model)

            fakenodo_service.publish_deposition(deposition_id)
            doi = fakenodo_service.get_doi(deposition_id)
            base_doi_mapping_repository.create(dataset.ds_meta_data_id, dataset_doi_old=doi)
            dsmetadata_service.update(dataset.ds_meta_data_id, dataset_doi=doi)

        except Exception as e:
            msg = f"Error uploading to Fakenodo: {e}"
            logger.error(msg)
            return jsonify({"message": msg}), 400

    return jsonify({"message": "Dataset published successfully", "redirect": url_for("basedataset.list_dataset")}), 200


@fooddataset_bp.route("/dataset/edit/<int:dataset_id>", methods=["GET", "POST"])
@login_required
def edit_doi_dataset(dataset_id):
    dataset = food_service.get_or_404(dataset_id)

    form = FoodDatasetForm()

    temp_folder = current_user.temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    working_dir = os.getenv("WORKING_DIR", "")
    dataset_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")

    if request.method == "POST":
        if not form.food_models.entries[0].filename.data:
            form.food_models = []

        result, errors = food_service.edit_doi_dataset(dataset, form)
        return food_service.handle_service_response(
            result, errors, "basedataset.list_dataset", "Dataset updated", "dataset/edit_dataset.html", form
        )
    else:
        for food_model in dataset.files:
            for file in food_model.files:
                src_file = os.path.join(dataset_dir, file.name)
                dest_file = os.path.join(temp_folder, file.name)

                if not os.path.exists(src_file):
                    continue

                if os.path.exists(dest_file):
                    base_name, ext = os.path.splitext(file.name)
                    i = 1
                    while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){ext}")):
                        i += 1
                    dest_file = os.path.join(temp_folder, f"{base_name} ({i}){ext}")

                shutil.copy(src_file, dest_file)

        form.title.data = dataset.ds_meta_data.title
        form.desc.data = dataset.ds_meta_data.description
        form.publication_type.data = dataset.ds_meta_data.publication_type.value
        form.publication_doi.data = dataset.ds_meta_data.publication_doi
        form.tags.data = dataset.ds_meta_data.tags
        form.desc.data = dataset.ds_meta_data.description

        form.authors.entries = []
        for author in dataset.ds_meta_data.authors:
            author_subform = AuthorForm()
            author_subform.name.data = author.name
            author_subform.affiliation.data = author.affiliation
            author_subform.orcid.data = author.orcid
            form.authors.append_entry(author_subform.data)

        form.food_models.entries = []
        for food_model in dataset.files:
            file_subform = FoodModelForm()
            file_subform.filename.data = food_model.food_meta_data.food_filename
            file_subform.title.data = food_model.food_meta_data.title
            file_subform.description = food_model.food_meta_data.description
            file_subform.publication_type = food_model.food_meta_data.publication_type
            file_subform.publication_doi = food_model.food_meta_data.publication_doi
            file_subform.tags = food_model.food_meta_data.tags

            file_subform.authors.entries = []
            for file_author in food_model.food_meta_data.authors:
                file_author_subform = AuthorForm()
                file_author_subform.name.data = file_author.name
                file_author_subform.affiliation.data = file_author.affiliation
                file_author_subform.orcid.data = file_author.orcid
                file_subform.authors.append_entry(file_author_subform.data)

            form.food_models.append_entry(file_subform)

    return render_template("fooddataset/edit_dataset.html", form=form, dataset=dataset)


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


@fooddataset_bp.route("/dataset/trending", methods=["GET"])
def trending_datasets():
    try:
        period = request.args.get("period", "week")
        limit = request.args.get("limit", 10, type=int)

        limit = min(limit, 50)

        if period == "month":
            trending = food_service.get_trending_monthly(limit=limit)
            period_label = "This Month"
        else:
            trending = food_service.get_trending_weekly(limit=limit)
            period_label = "This Week"

        return render_template("fooddataset/trending.html", trending=trending, period=period, period_label=period_label)
    except Exception as e:
        logger.error(f"Error getting trending datasets: {e}")
        return render_template("fooddataset/trending.html", trending=[], error=str(e))


@fooddataset_bp.route("/dataset/<int:dataset_id>/view", methods=["POST"])
def register_view(dataset_id):
    try:
        success = food_service.register_dataset_view(dataset_id)

        if success:
            return jsonify({"success": True, "message": "View registered"}), 200
        else:
            return jsonify({"success": False, "message": "Dataset not found"}), 404

    except Exception as e:
        logger.error(f"Error registering view for dataset {dataset_id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@fooddataset_bp.route("/dataset/<int:dataset_id>/download", methods=["POST"])
def register_download(dataset_id):
    try:
        success = food_service.register_dataset_download(dataset_id)

        if success:
            return jsonify({"success": True, "message": "Download registered"}), 200
        else:
            return jsonify({"success": False, "message": "Dataset not found"}), 404

    except Exception as e:
        logger.error(f"Error registering download for dataset {dataset_id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@fooddataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file:
        return jsonify({"message": "No file provided"}), 400

    filename = file.filename or ""
    lower = filename.lower()

    # If the uploaded file is a ZIP, delegate to upload_zip
    if lower.endswith(".zip"):
        # emulate request.files for upload_zip by temporarily setting file in request
        # but simplest is to call the upload_zip logic directly
        return upload_zip()

    if not (lower.endswith(".food")):
        return jsonify({"message": "Please upload a .food file"}), 400

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
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

    return (
        jsonify(
            {
                "message": "UVL uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@fooddataset_bp.route("/dataset/file/upload_zip", methods=["POST"])
@login_required
def upload_zip():
    """Accept a ZIP file upload, extract files into the user's temp folder and
    return a list of saved filenames. Only regular files are extracted; directories
    are skipped. Collisions are resolved by appending ` (n)` like the single file upload.
    """
    if "file" not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files["file"]
    if not file or not file.filename.lower().endswith(".zip"):
        return jsonify({"message": "No valid zip file"}), 400

    temp_folder = current_user.temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        file.save(tmp.name)

        saved_files = []
        with ZipFile(tmp.name, "r") as z:
            for member in z.namelist():
                if member.endswith("/"):
                    continue

                member_basename = os.path.basename(member)
                if not member_basename:
                    continue

                dest_path = os.path.join(temp_folder, member_basename)

                base_name, extension = os.path.splitext(member_basename)
                i = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(temp_folder, f"{base_name} ({i}){extension}")
                    i += 1

                # Extract member to the destination
                with z.open(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                saved_files.append(os.path.basename(dest_path))

        if not saved_files:
            return jsonify({"message": "No files extracted from the ZIP"}), 400

        return jsonify({"message": "ZIP extracted successfully", "filenames": saved_files}), 200
    except Exception as e:
        logger.exception("Error extracting zip file: %s", e)
        return jsonify({"message": str(e)}), 500
    finally:
        try:
            tmp.close()
            os.unlink(tmp.name)
        except Exception:
            pass


@fooddataset_bp.route("/dataset/file/upload_github", methods=["POST"])
@login_required
def upload_github():
    """Download a GitHub repository as a ZIP and extract files into the user's temp folder.

    Accepts form/json params:
      - repo: "owner/repo" (optional if zip_url provided)
      - branch: branch name (optional, defaults to 'main')
      - zip_url: full URL to a zip (optional, overrides repo/branch)
    Returns JSON with list of saved filenames.
    """
    data = request.form.to_dict() or (request.get_json(silent=True) or {})
    repo = data.get("repo")
    branch = data.get("branch") or "main"
    zip_url = data.get("zip_url")

    if not zip_url:
        if not repo:
            return jsonify({"message": "Provide 'repo' (owner/repo) or 'zip_url'"}), 400
        zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"

    if "github.com" not in zip_url:
        return jsonify({"message": "Only GitHub zip URLs are supported"}), 400

    temp_folder = current_user.temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        # download the zip
        with urllib.request.urlopen(zip_url) as resp:
            if getattr(resp, "status", None) and resp.status >= 400:
                return jsonify({"message": f"Failed to download zip: HTTP {resp.status}"}), 400
            with open(tmp.name, "wb") as out:
                shutil.copyfileobj(resp, out)

        # extract files as in upload_zip
        saved_files = []
        with ZipFile(tmp.name, "r") as z:
            for member in z.namelist():
                if member.endswith("/"):
                    continue
                member_basename = os.path.basename(member)
                if not member_basename:
                    continue

                dest_path = os.path.join(temp_folder, member_basename)
                base_name, extension = os.path.splitext(member_basename)
                i = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(temp_folder, f"{base_name} ({i}){extension}")
                    i += 1

                with z.open(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                saved_files.append(os.path.basename(dest_path))

        if not saved_files:
            return jsonify({"message": "No files extracted from the GitHub ZIP"}), 400

        return jsonify({"message": "GitHub repo extracted successfully", "filenames": saved_files}), 200
    except urllib.error.HTTPError as he:
        logger.exception("HTTPError downloading GitHub zip: %s", he)
        if he.code == 404:
            return jsonify({"message": "GitHub repository or Branch not found"}), 400
        else:
            return jsonify({"message": f"HTTP error: {he.code}"}), 400
    except Exception as e:
        logger.exception("Error downloading/extracting GitHub zip: %s", e)
        return jsonify({"message": str(e)}), 500
    finally:
        try:
            tmp.close()
            os.unlink(tmp.name)
        except Exception:
            pass
