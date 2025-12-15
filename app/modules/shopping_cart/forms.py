from flask_wtf import FlaskForm
from wtforms import SubmitField


class ShoppingCartForm(FlaskForm):
    submit = SubmitField("Save shopping_cart")
