from flask_wtf import FlaskForm
from wtforms import SubmitField


class ZFakenodoForm(FlaskForm):
    submit = SubmitField("Save fakenodo")
