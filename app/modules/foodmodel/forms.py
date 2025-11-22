from flask_wtf import FlaskForm
from wtforms import SubmitField


class FoodmodelForm(FlaskForm):
    submit = SubmitField('Save foodmodel')
