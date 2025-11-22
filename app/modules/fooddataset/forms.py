from flask_wtf import FlaskForm
from wtforms import SubmitField


class FooddatasetForm(FlaskForm):
    submit = SubmitField('Save fooddataset')
