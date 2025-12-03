from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.modules.shopping_cart.services import ShoppingCartService
from app.modules.dataset.services import DataSetService

from app.modules.shopping_cart import shopping_cart_bp

shopping_cart_service = ShoppingCartService()
dataset_service = DataSetService()

@shopping_cart_bp.route('/shopping_cart', methods=['GET'])
@login_required
def get_shopping_cart_from_current_user():
    cart = shopping_cart_service.get_by_user(current_user.id)

    return render_template('shopping_cart/index.html', cart=cart)

@shopping_cart_bp.route('/shopping_cart/add/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def add_dataset_to_cart(dataset_id):
    shopping_cart_service.add_to_cart(current_user.id, dataset_id)
    cart = shopping_cart_service.get_by_user(current_user.id)
    return redirect(request.referrer or '/')

@shopping_cart_bp.route('/shopping_cart/remove/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def remove_dataset_from_cart(dataset_id):
    shopping_cart_service.remove_from_cart(current_user.id, dataset_id)
    cart = shopping_cart_service.get_by_user(current_user.id)
    return render_template('shopping_cart/index.html', cart=cart)



