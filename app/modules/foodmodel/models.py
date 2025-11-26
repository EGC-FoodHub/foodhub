from sqlalchemy import Enum as SQLAlchemyEnum

from app import db
from app.modules.basedataset.models import BaseAuthor, BasePublicationType


class FoodModel(db.Model):
    """
    Representa un único archivo .food dentro de un FoodDataset.
    Equivalente a FeatureModel.
    """

    __tablename__ = "food_model"

    id = db.Column(db.Integer, primary_key=True)

    # Relación al dataset padre
    data_set_id = db.Column(db.Integer, db.ForeignKey("food_dataset.id"), nullable=False)

    # Relación a metadatos específicos
    food_meta_data_id = db.Column(db.Integer, db.ForeignKey("food_meta_data.id"))

    # Archivos asociados (.food)
    files = db.relationship("Hubfile", backref="food_model", lazy=True, cascade="all, delete")

    # Metadata específica
    food_meta_data = db.relationship("FoodMetaData", uselist=False, backref="food_model", cascade="all, delete")

    dataset = db.relationship("app.modules.fooddataset.models.FoodDataset", back_populates="files")

    def __repr__(self):
        return f"FoodModel<{self.id}>"


class FoodMetaData(db.Model):
    """
    Contiene los metadatos extraídos del archivo .food
    Equivalente a FMMetaData
    """

    __tablename__ = "food_meta_data"

    id = db.Column(db.Integer, primary_key=True)

    # Datos propios del alimento
    food_filename = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    food_type = db.Column(db.String(50), nullable=True)  # VEGAN, VEGETARIAN, etc.
    calories = db.Column(db.String(50), nullable=True)

    description = db.Column(db.Text, nullable=True)

    publication_type = db.Column(SQLAlchemyEnum(BasePublicationType), nullable=True)
    publication_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))

    # Relación a métricas nutricionales
    food_metrics_id = db.Column(db.Integer, db.ForeignKey("food_metrics.id"))
    food_metrics = db.relationship("FoodMetrics", uselist=False, backref="food_meta_data")

    # Autores (igual que FMMetaData)
    authors = db.relationship(
        "app.modules.basedataset.models.BaseAuthor",
        backref="food_metadata",
        lazy=True,
        cascade="all, delete",
        foreign_keys=[BaseAuthor.food_meta_data_id],  # necesitas añadir esta columna al modelo Author
    )

    def __repr__(self):
        return f"FoodMetaData<{self.title}>"


class FoodMetrics(db.Model):
    """
    Métricas nutricionales del alimento.
    Equivalente a FMMetrics.
    """

    __tablename__ = "food_metrics"

    id = db.Column(db.Integer, primary_key=True)

    # Métricas desglosadas
    protein = db.Column(db.String(20))
    carbohydrates = db.Column(db.String(20))
    fat = db.Column(db.String(20))
    fiber = db.Column(db.String(20))
    vitamin_e = db.Column(db.String(20))
    magnesium = db.Column(db.String(20))
    calcium = db.Column(db.String(20))

    def __repr__(self):
        return f"FoodMetrics<protein={self.protein}, fat={self.fat}>"
