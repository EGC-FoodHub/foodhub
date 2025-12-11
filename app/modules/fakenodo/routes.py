'''
import datetime
import uuid

from flask import jsonify, render_template, request

from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.services import FakenodoService

service = FakenodoService()


@fakenodo_bp.route("/fakenodo", methods=["GET"])
def index():
    return render_template("fakenodo/index.html")


@fakenodo_bp.route("/fakenodo/test", methods=["GET"])
def fakenodo_test() -> dict:
    return service.test_full_connection()


@fakenodo_bp.route("/fakenodo/dummy", methods=["GET", "POST", "PUT", "DELETE"])
def dummy():
    if request.method == "POST":
        return jsonify({"status": "created", "id": "1", "message": "dummy endpoint"}), 201
    elif request.method == "DELETE":
        return jsonify({"status": "deleted", "message": "dummy endpoint"}), 204
    else:
        return jsonify({"status": "ok", "message": "dummy endpoint"}), 200


@fakenodo_bp.route("/fakenodo/dummy/1/files", methods=["GET", "POST", "PUT", "DELETE"])
def files_dummy():
    if request.method == "POST":
        return jsonify({"status": "created", "id": "1", "message": "dummy endpoint"}), 201
    elif request.method == "DELETE":
        return jsonify({"status": "deleted", "message": "dummy endpoint"}), 204
    else:
        return jsonify({"status": "ok", "message": "dummy endpoint"}), 200


@fakenodo_bp.route("/fakenodo/dummy/1", methods=["DELETE"])
def delete_dummy():
    return jsonify({"status": "deleted", "message": "dummy endpoint"}), 204


record_dict = {}


@fakenodo_bp.route("/fakenodo/records", methods=["POST", "GET"])
def records():
    if request.method == "GET":
        return jsonify(list(record_dict.values())), 200

    elif request.method == "POST":
        data = request.json or {}
        record_id = str(uuid.uuid4())[:8]
        doi = service.generate_doi()
        record = {
            "id": record_id,
            "doi": doi,
            "metadata": data.get("metadata", {}),
            "files": data.get("files", []),
            "version": 1,
            "created": datetime.datetime.utcnow().isoformat(),
            "published": False,
        }
        record_dict[record_id] = record
        return jsonify(record), 201


@fakenodo_bp.route("/fakenodo/records/<id>", methods=["PUT", "GET"])
def records_data(id):
    record = record_dict.get(id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    if request.method == "GET":
        return jsonify(record), 200

    elif request.method == "PUT":
        data = request.json or {}
        record["metadata"].update(data.get("metadata", {}))
        return jsonify(record), 200


@fakenodo_bp.route("/fakenodo/records/<id>/publish", methods=["POST"])
def records_publish(id):
    record = record_dict.get(id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    new_version = int(record["version"]) + 1
    new_doi = service.generate_doi(new_version)

    record["version"] = new_version
    record["doi"] = new_doi
    record["published"] = True
    record["created"] = datetime.datetime.utcnow().isoformat()
 esto era lo de antes
    new_record = {
        "id": record["id"],
        "doi": new_doi,
        "metadata": record["metadata"],
        "files": record["files"],
        "version": new_version,
        "created": datetime.datetime.utcnow().isoformat(),
        "published": True,
    }

    record_dict[new_record["id"]] = new_record
esto era lo de antes
    return jsonify(new_record), 201


@fakenodo_bp.route("/fakenodo/records/<id>/files", methods=["POST"])
def records_files(id):
    record = record_dict.get(id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    data = request.json or {}
    files = data.get("files", [])
    record["files"].extend(files)
    return jsonify({"status": "files added", "files": record["files"]}), 200


@fakenodo_bp.route("/fakenodo/view")
def view_records():
    return render_template("fakenodo/records.html")
'''
import datetime
import uuid
from flask import jsonify, render_template, request
from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.services import FakenodoService

service = FakenodoService()

# Diccionario global simulando DB
record_dict = {}


@fakenodo_bp.route("/fakenodo", methods=["GET"])
def index():
    return render_template("fakenodo/index.html")


@fakenodo_bp.route("/fakenodo/test", methods=["GET"])
def fakenodo_test() -> dict:
    return service.test_full_connection()

# Crear o listar records
@fakenodo_bp.route("/fakenodo/records", methods=["POST", "GET"])
def records():
    if request.method == "GET":
        return jsonify(list(record_dict.values())), 200

    elif request.method == "POST":
        data = request.json or {}
        record_id = str(uuid.uuid4())[:8]
        doi = service.generate_doi()
        record = {
            "id": record_id,
            "doi": doi,
            "metadata": data.get("metadata", {}),  # Guardamos todo metadata
            "files": data.get("files", []),
            "version": 1,
            "created": datetime.datetime.utcnow().isoformat(),
            "published": False,
        }
        record_dict[record_id] = record
        return jsonify(record), 201

# Obtener o actualizar un record
@fakenodo_bp.route("/fakenodo/records/<id>", methods=["GET", "PUT"])
def records_data(id):
    record = record_dict.get(id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    if request.method == "GET":
        return jsonify(record), 200

    elif request.method == "PUT":
        data = request.json or {}
        record["metadata"].update(data.get("metadata", {}))
        return jsonify(record), 200

# Publicar un record (simula DOI y versión)
@fakenodo_bp.route("/fakenodo/records/<id>/publish", methods=["POST"])
def records_publish(id):
    record = record_dict.get(id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    new_version = record["version"] + 1
    new_doi = service.generate_doi(new_version)

    record["version"] = new_version
    record["doi"] = new_doi
    record["published"] = True
    record["created"] = datetime.datetime.utcnow().isoformat()

    return jsonify(record), 201

# Subir archivos a un record
@fakenodo_bp.route("/fakenodo/records/<id>/files", methods=["POST"])
def records_files(id):
    record = record_dict.get(id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    data = request.json or {}
    files = data.get("files", [])
    record["files"].extend(files)
    return jsonify({"status": "files added", "files": record["files"]}), 200
