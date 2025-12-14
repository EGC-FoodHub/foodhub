import re
from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, SelectField, StringField, TextAreaField, SubmitField
from wtforms.validators import URL, DataRequired, Length, Optional

from flask_wtf.file import FileAllowed, FileField

from app.modules.basedataset.forms import AuthorForm, BaseDatasetForm
from app.modules.basedataset.models import BasePublicationType


class FoodModelForm(FlaskForm):

    filename = StringField("Filename", validators=[Optional()])

    title = StringField("Title", validators=[Optional(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])

    publication_type = SelectField(
        "Publication type",
        choices=[(pt.value, pt.name.replace("_", " ").title()) for pt in BasePublicationType],
        validators=[Optional()],
    )

    publication_doi = StringField("Publication DOI", validators=[Optional(), URL()])
    tags = StringField("Tags (separated by commas)", validators=[Optional()])

    authors = FieldList(FormField(AuthorForm))

    class Meta:
        csrf = False

    def get_authors(self):
        return [author.get_author() for author in self.authors]

    def get_food_metadata(self):
        return {
            "food_filename": self.filename.data,
            "title": self.title.data,
            "description": self.description.data,
            "publication_type": self.publication_type.data,
            "publication_doi": self.publication_doi.data,
            "tags": self.tags.data,
        }


class FoodDatasetForm(BaseDatasetForm):

    calories = StringField(
        "Calories", validators=[Optional(), Length(max=50)], description="Total calories (e.g., '2000 kcal')"
    )

    type = StringField(
        "Food Type",
        validators=[Optional(), Length(max=50)],
        description="Type of food (e.g., 'Breakfast', 'Lunch', 'Dinner')",
    )

    community = StringField(
        "Community",
        validators=[Optional(), Length(max=200)],
        description="Community or research group associated with this dataset",
    )

    food_models = FieldList(FormField(FoodModelForm), min_entries=1)

    import_method = StringField("Import method", default="manual")

    # --- Campo para subir el ZIP ---
    zip_file = FileField("ZIP Archive", validators=[Optional(), FileAllowed(["zip"], "Only .zip files are allowed!")])

    # --- Campo para la URL de GitHub ---
    github_url = StringField(
        "GitHub Repository URL",
        validators=[Optional(), URL()],
        render_kw={"placeholder": "https://github.com/user/repo"},
    )

    def get_dsmetadata(self):

        base_metadata = super().get_dsmetadata()

        food_metadata = {
            "calories": self.calories.data,
            "type": self.type.data,
            "community": self.community.data,
        }

        return {**base_metadata, **food_metadata}

    def get_food_models_metadata(self):

        return [fm.get_food_metadata() for fm in self.food_models]

    def validate(self, extra_validators=None):
        if not super(FoodDatasetForm, self).validate(extra_validators):
            return False

        is_valid = True
        method = self.import_method.data

        models_are_present = any(fm.filename.data for fm in self.food_models)

        if method == "manual":
            if not models_are_present:
                self.food_models.errors.append(
                    "At least one .food file is required for manual upload."
                )
                is_valid = False

        elif method == "zip":
            if not models_are_present:
                if not self.zip_file.data:
                    self.zip_file.errors.append(
                        "A ZIP file is required for this import method."
                    )
                    is_valid = False

        elif method == "github":
            if not models_are_present:
                if not self.github_url.data:
                    self.github_url.errors.append(
                        "A GitHub URL is required for this import method."
                    )
                    is_valid = False
                elif not re.match(r"^https://github\.com/[^/]+/[^/]+/?$", self.github_url.data):
                    self.github_url.errors.append(
                        "Invalid GitHub URL. Must be like https://github.com/user/repo"
                    )
                    is_valid = False

        # Validación final de seguridad
        if not models_are_present and is_valid:
            self.food_models.errors.append(
                "At least one food model is required"
            )
            is_valid = False

        return is_valid

    submit = SubmitField("Submit")
