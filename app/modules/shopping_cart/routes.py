from flask import render_template
from app.modules.shopping_cart import shopping_cart_bp


@shopping_cart_bp.route('/shopping_cart', methods=['GET'])
def index():
    return render_template('shopping_cart/index.html')
