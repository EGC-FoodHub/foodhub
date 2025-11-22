from flask import render_template

from app.modules.foodmodel import foodmodel_bp


@foodmodel_bp.route("/foodmodel", methods=["GET"])
def index():
    return render_template("foodmodel/index.html")
