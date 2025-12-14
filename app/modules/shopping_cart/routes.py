from flask import redirect, render_template, request
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
