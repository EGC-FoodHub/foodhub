from flask_wtf import FlaskForm
from wtforms import SubmitField


class FoodCheckerForm(FlaskForm):
    submit = SubmitField('Save food_checker')
