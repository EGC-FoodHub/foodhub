from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FieldList, FormField, SelectField
from wtforms.validators import DataRequired, Optional, URL

from app.modules.dataset.models import PublicationType


# -------------------------------------------------------------------
# Generic Author Form
# -------------------------------------------------------------------
class AuthorForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    affiliation = StringField("Affiliation", validators=[Optional()])
    orcid = StringField("ORCID", validators=[Optional()])
    gnd = StringField("GND", validators=[Optional()])

    class Meta:
        csrf = False  # subform does not need CSRF

    def get_author(self) -> dict:
        return {
            "name": self.name.data,
            "affiliation": self.affiliation.data,
            "orcid": self.orcid.data,
            "gnd": self.gnd.data,
        }


# -------------------------------------------------------------------
# Generic Dataset Metadata Form
# (Each dataset type will extend this)
# -------------------------------------------------------------------
class BaseDatasetForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    desc = TextAreaField("Description", validators=[DataRequired()])
    
    publication_type = SelectField(
        "Publication type",
        choices=[(pt.value, pt.name.replace("_", " ").title()) for pt in PublicationType],
        validators=[DataRequired()],
    )
    
    publication_doi = StringField("Publication DOI", validators=[Optional(), URL()])
    dataset_doi = StringField("Dataset DOI", validators=[Optional(), URL()])
    tags = StringField("Tags (comma-separated)", validators=[Optional()])

    authors = FieldList(FormField(AuthorForm), min_entries=1)

    class Meta:
        csrf = False

    # --------------------------
    # Helpers
    # --------------------------
    def get_authors(self) -> list:
        return [author.get_author() for author in self.authors]

    def convert_publication_type(self, raw_value: str) -> str:
        """Convert Enum value → Enum name for DB storage."""
        for pt in PublicationType:
            if pt.value == raw_value:
                return pt.name
        return "NONE"

    def get_metadata(self) -> dict:
        return {
            "title": self.title.data,
            "description": self.desc.data,
            "publication_type": self.convert_publication_type(self.publication_type.data),
            "publication_doi": self.publication_doi.data,
            "dataset_doi": self.dataset_doi.data,
            "tags": self.tags.data,
        }
