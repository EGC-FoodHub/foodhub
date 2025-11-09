import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile
from app.modules.dataset.food_trending_service import FoodTrendingService
from app.modules.dataset.models import DSViewRecord, FoodDataset
from datetime import timedelta  

from flask import (
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app import db 
from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import DSDownloadRecord
from app.modules.dataset.food_trending_service import FoodTrendingService
from app.modules.dataset.trending_formatter import TrendingFormatter
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
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

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each feature model (one feature model = one request to Zenodo)
                for feature_model in dataset.feature_models:
                    zenodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


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
        
        # Si es dataset de comida, actualizar métricas después de la descarga
        if hasattr(dataset, 'kind') and dataset.kind == "food":
            food_dataset = FoodDataset.query.get(dataset_id)
            if food_dataset:
                food_dataset.update_food_metrics()

    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.data_set
    
    # Registrar vista (nuevo código)
    user_cookie = request.cookies.get('view_cookie')
    if not user_cookie:
        user_cookie = str(uuid.uuid4())
    
    existing_view = DSViewRecord.query.filter(
        DSViewRecord.dataset_id == dataset.id,
        DSViewRecord.view_cookie == user_cookie,
        DSViewRecord.view_date >= datetime.now(timezone.utc) - timedelta(hours=1)
    ).first()
    
    if not existing_view:
        view_record = DSViewRecord(
            dataset_id=dataset.id,
            user_id=current_user.id if current_user.is_authenticated else None,
            view_date=datetime.now(timezone.utc),
            view_cookie=user_cookie
        )
        db.session.add(view_record)
        db.session.commit()
    
    # Si es dataset de comida, actualizar métricas
    if hasattr(dataset, 'kind') and dataset.kind == "food":
        food_dataset = FoodDataset.query.get(dataset.id)
        if food_dataset:
            food_dataset.update_food_metrics()

    # Save the cookie to the user's browser
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    if not request.cookies.get('view_cookie'):
        resp.set_cookie('view_cookie', user_cookie)

    return resp@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)
    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.data_set
    
    # Registrar vista (nuevo código)
    user_cookie = request.cookies.get('view_cookie')
    if not user_cookie:
        user_cookie = str(uuid.uuid4())
    
    existing_view = DSViewRecord.query.filter(
        DSViewRecord.dataset_id == dataset.id,
        DSViewRecord.view_cookie == user_cookie,
        DSViewRecord.view_date >= datetime.now(timezone.utc) - timedelta(hours=1)
    ).first()
    
    if not existing_view:
        view_record = DSViewRecord(
            dataset_id=dataset.id,
            user_id=current_user.id if current_user.is_authenticated else None,
            view_date=datetime.now(timezone.utc),
            view_cookie=user_cookie
        )
        db.session.add(view_record)
        db.session.commit()
    
    # Si es dataset de comida, actualizar métricas
    if hasattr(dataset, 'kind') and dataset.kind == "food":
        food_dataset = FoodDataset.query.get(dataset.id)
        if food_dataset:
            food_dataset.update_food_metrics()

    # Save the cookie to the user's browser
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    if not request.cookies.get('view_cookie'):
        resp.set_cookie('view_cookie', user_cookie)

    return resp

@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    return render_template("dataset/view_dataset.html", dataset=dataset)

# ==========================================================
# TRENDING DATASETS ROUTES (VERSIÓN CORREGIDA)
# ==========================================================

@dataset_bp.route("/dataset/<int:dataset_id>/view")
def view_dataset(dataset_id):
    """Ruta para visualizar dataset y registrar vista"""
    dataset = dataset_service.get_or_404(dataset_id)
    
    # Registrar vista
    user_cookie = request.cookies.get('view_cookie')
    if not user_cookie:
        user_cookie = str(uuid.uuid4())
    
    # Verificar si ya existe un registro de vista reciente para este cookie
    existing_view = DSViewRecord.query.filter(
        DSViewRecord.dataset_id == dataset_id,
        DSViewRecord.view_cookie == user_cookie,
        DSViewRecord.view_date >= datetime.now(timezone.utc) - timedelta(hours=1)
    ).first()
    
    if not existing_view:
        view_record = DSViewRecord(
            dataset_id=dataset_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            view_date=datetime.now(timezone.utc),
            view_cookie=user_cookie
        )
        db.session.add(view_record)
        db.session.commit()
    
    # Si es dataset de comida, actualizar métricas
    if hasattr(dataset, 'kind') and dataset.kind == "food":
        food_dataset = FoodDataset.query.get(dataset_id)
        if food_dataset:
            food_dataset.update_food_metrics()
    
    # Crear respuesta
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    if not request.cookies.get('view_cookie'):
        resp.set_cookie('view_cookie', user_cookie)
    
    return resp

@dataset_bp.route("/trending")
def trending_datasets():
    """Página principal de trending datasets"""
    trending_weekly = FoodTrendingService.get_weekly_trending(limit=10)
    trending_monthly = FoodTrendingService.get_monthly_trending(limit=10)
    most_recipes = FoodTrendingService.get_most_recipes_datasets(limit=5)
    rich_ingredients = FoodTrendingService.get_richest_ingredient_datasets(limit=5)
    
    return render_template(
        "dataset/trending.html",
        trending_weekly=trending_weekly,
        trending_monthly=trending_monthly,
        most_recipes=most_recipes,
        rich_ingredients=rich_ingredients
    )

@dataset_bp.route("/api/trending/weekly")
def api_trending_weekly():
    """API endpoint para trending semanal"""
    trending = FoodTrendingService.get_weekly_trending(limit=10)
    
    trending_data = []
    for dataset, downloads, views, recipes, score in trending:
        trending_data.append({
            "id": dataset.id,
            "name": dataset.name,
            "author": dataset.creator.username if dataset.creator else "Unknown",
            "downloads": downloads,
            "views": views,
            "recipes": recipes,
            "score": score,
            "url": url_for('dataset.view_dataset', dataset_id=dataset.id)
        })
    
    return jsonify({"trending_weekly": trending_data})

@dataset_bp.route("/api/trending/monthly")
def api_trending_monthly():
    """API endpoint para trending mensual"""
    trending = FoodTrendingService.get_monthly_trending(limit=10)
    
    trending_data = []
    for dataset, downloads, views, recipes, score in trending:
        trending_data.append({
            "id": dataset.id,
            "name": dataset.name,
            "author": dataset.creator.username if dataset.creator else "Unknown",
            "downloads": downloads,
            "views": views,
            "recipes": recipes,
            "score": score,
            "url": url_for('dataset.view_dataset', dataset_id=dataset.id)
        })
    
    return jsonify({"trending_monthly": trending_data})

@dataset_bp.route("/api/popular/recipes")
def api_popular_recipes():
    """API endpoint para datasets con más recetas"""
    datasets = FoodTrendingService.get_most_recipes_datasets(limit=10)
    
    datasets_data = []
    for dataset in datasets:
        datasets_data.append({
            "id": dataset.id,
            "name": dataset.name,
            "author": dataset.creator.username if dataset.creator else "Unknown",
            "total_recipes": dataset.total_recipes or 0,
            "total_ingredients": dataset.total_ingredients or 0,
            "url": url_for('dataset.view_dataset', dataset_id=dataset.id)
        })
    
    return jsonify({"popular_recipes": datasets_data})

# Añadir al final de routes.py, antes del cierre

@dataset_bp.route("/dataset/<int:dataset_id>/view")
def view_dataset(dataset_id):
    """Ruta para visualizar dataset y registrar vista"""
    dataset = dataset_service.get_or_404(dataset_id)
    
    # Registrar vista
    user_cookie = request.cookies.get('view_cookie')
    if not user_cookie:
        user_cookie = str(uuid.uuid4())
    
    # Verificar si ya existe un registro de vista reciente para este cookie
    existing_view = DSViewRecord.query.filter(
        DSViewRecord.dataset_id == dataset_id,
        DSViewRecord.view_cookie == user_cookie,
        DSViewRecord.view_date >= datetime.now(timezone.utc) - timedelta(hours=1)
    ).first()
    
    if not existing_view:
        view_record = DSViewRecord(
            dataset_id=dataset_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            view_date=datetime.now(timezone.utc),
            view_cookie=user_cookie
        )
        db.session.add(view_record)
        db.session.commit()
    
    # Si es dataset de comida, actualizar métricas
    if hasattr(dataset, 'dataset_kind') and dataset.dataset_kind == "food":
        food_dataset = FoodDataset.query.get(dataset_id)
        if food_dataset:
            food_dataset.update_food_metrics()
    
    # Crear respuesta
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    if not request.cookies.get('view_cookie'):
        resp.set_cookie('view_cookie', user_cookie)
    
    return resp

@dataset_bp.route("/trending")
def trending_datasets():
    """Página principal de trending datasets"""
    trending_weekly = FoodTrendingService.get_weekly_trending(limit=10)
    trending_monthly = FoodTrendingService.get_monthly_trending(limit=10)
    most_recipes = FoodTrendingService.get_most_recipes_datasets(limit=5)
    rich_ingredients = FoodTrendingService.get_richest_ingredient_datasets(limit=5)
    
    return render_template(
        "dataset/trending.html",
        trending_weekly=trending_weekly,
        trending_monthly=trending_monthly,
        most_recipes=most_recipes,
        rich_ingredients=rich_ingredients
    )

@dataset_bp.route("/api/trending/weekly")
def api_trending_weekly():
    """API endpoint para trending semanal"""
    trending = FoodTrendingService.get_weekly_trending(limit=10)
    
    trending_data = []
    for dataset, downloads, views, recipes, score in trending:
        trending_data.append({
            "id": dataset.id,
            "name": dataset.name(),
            "author": dataset.user.username if dataset.user else "Unknown",
            "downloads": downloads,
            "views": views,
            "recipes": recipes,
            "score": score,
            "url": url_for('dataset.view_dataset', dataset_id=dataset.id)
        })
    
    return jsonify({"trending_weekly": trending_data})

@dataset_bp.route("/api/trending/monthly")
def api_trending_monthly():
    """API endpoint para trending mensual"""
    trending = FoodTrendingService.get_monthly_trending(limit=10)
    
    trending_data = []
    for dataset, downloads, views, recipes, score in trending:
        trending_data.append({
            "id": dataset.id,
            "name": dataset.name(),
            "author": dataset.user.username if dataset.user else "Unknown",
            "downloads": downloads,
            "views": views,
            "recipes": recipes,
            "score": score,
            "url": url_for('dataset.view_dataset', dataset_id=dataset.id)
        })
    
    return jsonify({"trending_monthly": trending_data})



# RUTAS NUEVAS Y MEJORADAS - Añadir después de tus rutas existentes

@dataset_bp.route("/trending")
def trending_datasets():
    """Página principal de trending datasets - VERSIÓN MEJORADA"""
    try:
        # Obtener datos formateados
        weekly_downloads = FoodTrendingService.get_trending_by_downloads(timeframe='week', limit=10)
        monthly_downloads = FoodTrendingService.get_trending_by_downloads(timeframe='month', limit=10)
        weekly_views = FoodTrendingService.get_trending_by_views(timeframe='week', limit=10)
        most_recipes = FoodTrendingService.get_most_recipes_datasets(limit=10)
        rich_ingredients = FoodTrendingService.get_richest_ingredient_datasets(limit=10)
        
        # Formatear para la vista
        formatted_data = {
            'weekly_downloads': TrendingFormatter.format_trending_list(weekly_downloads, 'downloads'),
            'monthly_downloads': TrendingFormatter.format_trending_list(monthly_downloads, 'downloads'),
            'weekly_views': TrendingFormatter.format_trending_list(weekly_views, 'views'),
            'most_recipes': TrendingFormatter.format_trending_list(most_recipes, 'recipes'),
            'rich_ingredients': TrendingFormatter.format_trending_list(rich_ingredients, 'ingredients')
        }
        
        return render_template(
            "dataset/trending.html",
            trending=formatted_data,
            title="Trending Datasets"
        )
    except Exception as e:
        print(f"Error loading trending page: {e}")
        return render_template("error.html", 
                             message="Error loading trending datasets. Please try again later."), 500

@dataset_bp.route("/api/trending/<timeframe>")
def api_trending(timeframe):
    """API endpoint único para trending - VERSIÓN MEJORADA"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)  # Máximo 50 items
        
        if timeframe == 'weekly':
            trending_data = FoodTrendingService.get_trending_by_downloads(timeframe='week', limit=limit)
            metric_type = 'downloads'
        elif timeframe == 'monthly':
            trending_data = FoodTrendingService.get_trending_by_downloads(timeframe='month', limit=limit)
            metric_type = 'downloads'
        elif timeframe == 'views':
            trending_data = FoodTrendingService.get_trending_by_views(timeframe='week', limit=limit)
            metric_type = 'views'
        else:
            return jsonify({"error": "Invalid timeframe. Use 'weekly', 'monthly', or 'views'"}), 400
        
        response_data = TrendingFormatter.format_api_response(trending_data, metric_type)
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dataset_bp.route("/api/trending/recipes/most")
def api_most_recipes():
    """API endpoint para datasets con más recetas"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        datasets = FoodTrendingService.get_most_recipes_datasets(limit=limit)
        
        response_data = TrendingFormatter.format_api_response(datasets, 'recipes')
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dataset_bp.route("/api/trending/ingredients/rich")
def api_rich_ingredients():
    """API endpoint para datasets con más ingredientes"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        datasets = FoodTrendingService.get_richest_ingredient_datasets(limit=limit)
        
        response_data = TrendingFormatter.format_api_response(datasets, 'ingredients')
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para el widget de trending en homepage
@dataset_bp.route("/api/homepage/trending")
def api_homepage_trending():
    """API específica para el widget de trending en homepage"""
    try:
        trending_data = FoodTrendingService.get_trending_for_homepage()
        
        formatted_response = {
            'weekly_downloads': TrendingFormatter.format_trending_list(
                trending_data['weekly_downloads'], 'downloads'
            ),
            'weekly_views': TrendingFormatter.format_trending_list(
                trending_data['weekly_views'], 'views'
            ),
            'most_recipes': TrendingFormatter.format_trending_list(
                trending_data['most_recipes'], 'recipes'
            ),
            'rich_ingredients': TrendingFormatter.format_trending_list(
                trending_data['rich_ingredients'], 'ingredients'
            )
        }
        
        return jsonify(formatted_response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500