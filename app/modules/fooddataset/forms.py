from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, SelectField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Optional

from app.modules.basedataset.forms import AuthorForm, BaseDatasetForm
from app.modules.basedataset.models import BasePublicationType


class FoodModelForm(FlaskForm):
    """
    Formulario para un archivo individual .food (un modelo).
    """

    filename = StringField("Filename", validators=[DataRequired()])

    title = StringField("Title", validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional()])

    publication_type = SelectField(
        "Publication type",
        choices=[(pt.value, pt.name.replace("_", " ").title()) for pt in BasePublicationType],
        validators=[Optional()],
    )

    publication_doi = StringField("Publication DOI", validators=[Optional(), URL()])
    tags = StringField("Tags (separated by commas)")

    authors = FieldList(FormField(AuthorForm))

    class Meta:
        csrf = False

    def get_authors(self):
        return [author.get_author() for author in self.authors]

    def get_food_metadata(self):
        """
        Devuelve el diccionario para crear el objeto FoodMetaData.
        Nombre corregido (antes get_fmmetadata).
        """
        return {
            "food_filename": self.filename.data,
            "title": self.title.data,
            "description": self.description.data,
            "publication_type": self.publication_type.data,
            "publication_doi": self.publication_doi.data,
            "tags": self.tags.data,
        }


class FoodDatasetForm(BaseDatasetForm):
    """
    Formulario principal para subir FoodDatasets.
    Hereda los campos de dataset (título, desc, autores) de BaseDatasetForm.
    Añade la lista de modelos de comida.
    """

    food_models = FieldList(FormField(FoodModelForm), min_entries=1)

    def get_food_models_metadata(self):
        return [fm.get_food_metadata() for fm in self.food_models]
