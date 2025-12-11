from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import URL, DataRequired, Optional

from app.modules.basedataset.models import BasePublicationType


class AuthorForm(FlaskForm):
    """
    Formulario reutilizable para autores.
    Se usa tanto para el dataset como para los modelos individuales.
    """

    name = StringField("Name", validators=[DataRequired()])
    affiliation = StringField("Affiliation")
    orcid = StringField("ORCID")
    gnd = StringField("GND")

    class Meta:
        csrf = False

    def get_author(self):
        return {
            "name": self.name.data,
            "affiliation": self.affiliation.data,
            "orcid": self.orcid.data,
        }


class BaseDatasetForm(FlaskForm):
    """
    Formulario Base con los metadatos comunes a cualquier dataset.
    NO incluye la lista de archivos/modelos (eso va en los hijos).
    """

    title = StringField("Title", validators=[DataRequired()])
    desc = TextAreaField("Description", validators=[DataRequired()])

    publication_type = SelectField(
        "Publication type",
        choices=[(pt.value, pt.name.replace("_", " ").title()) for pt in BasePublicationType],
        validators=[DataRequired()],
    )

    publication_doi = StringField("Publication DOI", validators=[Optional(), URL()])
    dataset_doi = StringField("Dataset DOI", validators=[Optional(), URL()])
    tags = StringField("Tags (separated by commas)")
    authors = FieldList(FormField(AuthorForm))
    submit = SubmitField("Submit")

    def get_dsmetadata(self):
        """
        Devuelve un diccionario listo para crear un objeto BaseDSMetaData (o hijos).
        """
        publication_type_converted = self.convert_publication_type(self.publication_type.data)

        return {
            "title": self.title.data,
            "description": self.desc.data,
            "publication_type": publication_type_converted,
            "publication_doi": self.publication_doi.data,
            "dataset_doi": self.dataset_doi.data,
            "tags": self.tags.data,
        }

    def convert_publication_type(self, value):
        for pt in BasePublicationType:
            if pt.value == value:
                return pt.name
        return "NONE"

    def get_authors(self):
        return [author.get_author() for author in self.authors]
