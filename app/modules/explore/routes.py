import os

from flask import Blueprint, jsonify, render_template, request, send_from_directory

from app.modules.explore.forms import ExploreForm
from app.modules.explore.services import ExploreService

explore_bp = Blueprint("explore", __name__, template_folder="templates")


@explore_bp.route("/explore/scripts.js")
def scripts():
    return send_from_directory(os.path.join(os.path.dirname(__file__), "assets"), "scripts.js")


@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    form = ExploreForm()
    if request.method == "GET":
        return render_template("explore/index.html", form=form)

    criteria = request.get_json()
    datasets = ExploreService().filter(**criteria)

    results = []
    for dataset in datasets:
        meta = dataset.ds_meta_data
        if not meta:
            continue

        authors_list = []
        if meta.authors:
            for author in meta.authors:
                authors_list.append(
                    {
                        "name": author.name,
                        "affiliation": author.affiliation if author.affiliation else "",
                        "orcid": author.orcid if author.orcid else "",
                    }
                )

        tags_list = []
        if meta.tags:
            tags_list = [t.strip() for t in meta.tags.split(",")]

        pub_type = meta.publication_type
        if hasattr(pub_type, "name"):
            pub_type = pub_type.name.replace("_", " ").title()

        size = "Unknown size"
        if hasattr(dataset, "total_size_in_human_format"):
            size = dataset.total_size_in_human_format

        results.append(
            {
                "id": dataset.id,
                "title": meta.title,
                "description": meta.description,
                "created_at": dataset.created_at.isoformat(),
                "url": f"/dataset/{dataset.id}",
                "publication_type": pub_type,
                "authors": authors_list,
                "tags": tags_list,
                "total_size_in_human_format": size,
            }
        )

    return jsonify(results)
