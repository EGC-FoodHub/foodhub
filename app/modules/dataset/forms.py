from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import FieldList, FormField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import URL, DataRequired, Optional

from app.modules.dataset.models import PublicationType


class AuthorForm(FlaskForm):
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


class FeatureModelForm(FlaskForm):
    uvl_filename = StringField("UVL Filename", validators=[DataRequired()])
    title = StringField("Title", validators=[Optional()])
    desc = TextAreaField("Description", validators=[Optional()])
    publication_type = SelectField(
        "Publication type",
        choices=[(pt.value, pt.name.replace("_", " ").title()) for pt in PublicationType],
        validators=[Optional()],
    )
    publication_doi = StringField("Publication DOI", validators=[Optional(), URL()])
    tags = StringField("Tags (separated by commas)")
    version = StringField("UVL Version")
    authors = FieldList(FormField(AuthorForm))

    class Meta:
        csrf = False  # disable CSRF because is subform

    def get_authors(self):
        return [author.get_author() for author in self.authors]

    def get_fmmetadata(self):
        return {
            "uvl_filename": self.uvl_filename.data,
            "title": self.title.data,
            "description": self.desc.data,
            "publication_type": self.publication_type.data,
            "publication_doi": self.publication_doi.data,
            "tags": self.tags.data,
            "uvl_version": self.version.data,
        }

    # Backwards-compatible name used elsewhere
    def get_feature_model(self):
        return self.get_fmmetadata()


class DataSetForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    desc = TextAreaField("Description", validators=[DataRequired()])
    publication_type = SelectField(
        "Publication type",
        choices=[(pt.value, pt.name.replace("_", " ").title()) for pt in PublicationType],
        validators=[DataRequired()],
    )
    publication_doi = StringField("Publication DOI", validators=[Optional(), URL()])
    dataset_doi = StringField("Dataset DOI", validators=[Optional(), URL()])
    tags = StringField("Tags (separated by commas)")
    authors = FieldList(FormField(AuthorForm))
    feature_models = FieldList(FormField(FeatureModelForm), min_entries=1)
    # method of import: manual (uploaded) or zip
    import_method = SelectField("Import method", choices=[("manual", "Manual"), ("zip", "ZIP")], default="manual")

    # --- Campo para subir el ZIP ---
    zip_file = FileField("ZIP Archive", validators=[Optional(), FileAllowed(["zip"], "Only .zip files are allowed!")])

    def validate(self, extra_validators=None):
        if not super(DataSetForm, self).validate(extra_validators):
            return False

        is_valid = True
        method = self.import_method.data

        if method == "manual":
            if not any(fm.uvl_filename.data for fm in self.feature_models):
                self.feature_models.errors.append("At least one UVL file is required for manual upload.")
                is_valid = False
        elif method == "zip":
            if not self.zip_file.data:
                self.zip_file.errors.append("A ZIP file is required for this import method.")
                is_valid = False

        return is_valid

    submit = SubmitField("Submit")

    def get_dsmetadata(self):

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
        for pt in PublicationType:
            if pt.value == value:
                return pt.name
        return "NONE"

    def get_authors(self):
        return [author.get_author() for author in self.authors]

    def get_feature_models(self):
        return [fm.get_feature_model() for fm in self.feature_models]
