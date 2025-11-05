from flask import render_template, jsonify, request

from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.services import FakenodoService


@fakenodo_bp.route("/fakenodo", methods=["GET"])
def index():
    return render_template("fakenodo/index.html")


@fakenodo_bp.route("/fakenodo/test", methods=["GET"])
def fakenodo_test() -> dict:
    service = FakenodoService()
    return service.test_full_connection()

@fakenodo_bp.route("/fakenodo/dummy", methods=["GET","POST","PUT","DELETE"])
def dummy():
    if request.method == "POST":
        return jsonify({"status":"created","id":"1","message":"dummy endpoint"}), 201
    elif request.method == "DELETE":
        return jsonify({"status":"deleted","message":"dummy endpoint"}), 204
    else:
        return jsonify({"status":"ok","message":"dummy endpoint"}), 200

@fakenodo_bp.route("/fakenodo/dummy/1/files", methods=["GET","POST","PUT","DELETE"])
def files_dummy():
    if request.method == "POST":
        return jsonify({"status":"created","id":"1","message":"dummy endpoint"}), 201
    elif request.method == "DELETE":
        return jsonify({"status":"deleted","message":"dummy endpoint"}), 204
    else:
        return jsonify({"status":"ok","message":"dummy endpoint"}), 200


@fakenodo_bp.route("/fakenodo/dummy/1", methods=["DELETE"])
def delete_dummy():
    return jsonify({"status":"deleted","message":"dummy endpoint"}), 204