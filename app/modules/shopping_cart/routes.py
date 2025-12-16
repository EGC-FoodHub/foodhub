from flask import redirect, render_template, request, abort
from flask_login import current_user, login_required

from app.modules.fooddataset.services import FoodDatasetService
from app.modules.shopping_cart import shopping_cart_bp
from app.modules.shopping_cart.services import ShoppingCartService

shopping_cart_service = ShoppingCartService()
food_dataset_service = FoodDatasetService()


@shopping_cart_bp.route("/shopping_cart", methods=["GET"])
@login_required
def get_shopping_cart_from_current_user():
    cart = shopping_cart_service.show_by_user(current_user.id)
    return render_template("shopping_cart/index.html", cart=cart)


@shopping_cart_bp.route("/shopping_cart/add/<int:food_dataset_id>", methods=["GET", "POST"])
@login_required
def add_dataset_to_cart(food_dataset_id):
    shopping_cart_service.add_to_cart(current_user.id, food_dataset_id)
    return redirect(request.referrer or "/")


@shopping_cart_bp.route("/shopping_cart/remove/<int:food_dataset_id>", methods=["GET", "POST"])
@login_required
def remove_dataset_from_cart(food_dataset_id):
    shopping_cart_service.remove_from_cart(current_user.id, food_dataset_id)
    cart = shopping_cart_service.get_by_user(current_user.id)
    return render_template("shopping_cart/index.html", cart=cart)


'''

APARTIR DE AQUI ES DE LA NUEVA IMPLEMENTACIÓN

'''


@shopping_cart_bp.route("/shopping_cart/history", methods=["GET"])
@login_required
def get_shopping_cart_history():
    """
    Muestra la pestaña de historial
    """
    history = shopping_cart_service.get_history_by_user(current_user.id)
    return render_template("shopping_cart/history.html", history=history)


@shopping_cart_bp.route("/shopping_cart/checkout", methods=["GET"])
@login_required
def checkout_cart():
    # Obtenemos el carrito para saber qué IDs vamos a descargar
    cart = shopping_cart_service.get_by_user(current_user.id)

    # Extraemos los IDs para construir la URL de descarga final
    dataset_ids = [str(ds.id) for ds in cart.food_data_sets]
    ids_param = ",".join(dataset_ids)

    # Guardamos el historial (Aquí se crea el registro en base de datos)
    shopping_cart_service.checkout(current_user.id)

    # Redirigimos a la ruta de descarga
    return redirect(f"/dataset/download?ids={ids_param}")


@shopping_cart_bp.route("/shopping_cart/history/<int:record_id>", methods=["GET"])
@login_required
def get_history_record_detail(record_id):
    # Buscamos el registro usando el servicio
    record = shopping_cart_service.get_history_record_by_id(record_id, current_user.id)

    # Si no existe 404
    if not record:
        abort(404)

    return render_template("shopping_cart/history_detail.html", record=record)
