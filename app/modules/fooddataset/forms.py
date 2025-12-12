from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, SelectField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Length, Optional

from app.modules.basedataset.forms import AuthorForm, BaseDatasetForm
from app.modules.basedataset.models import BasePublicationType


class FoodModelForm(FlaskForm):

    filename = StringField("Filename", validators=[DataRequired()])

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

        if not super().validate(extra_validators):
            return False

        if len(self.food_models) < 1:
            self.food_models.errors.append("At least one food model is required")
            return False

        return True
