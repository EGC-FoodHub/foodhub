from app import db
from app.modules.basedataset.models import BaseDataset, BaseDSMetaData


class FoodDataset(BaseDataset):
    __tablename__ = "food_dataset"

    id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"), primary_key=True)

    ds_meta_data_id = db.Column(
        db.Integer, db.ForeignKey("food_ds_meta_data.id", use_alter=True, name="fk_food_dataset_ds_metadata")
    )

    ds_meta_data = db.relationship(
        "FoodDSMetaData", back_populates="dataset", uselist=False, foreign_keys=[ds_meta_data_id]
    )

    files = db.relationship("FoodModel", back_populates="dataset", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_identity": "food_dataset",
    }

    def __repr__(self):
        return f"<FoodDataset {self.id}>"


class FoodDSMetaData(BaseDSMetaData):
    __tablename__ = "food_ds_meta_data"

    id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"), primary_key=True)
    calories = db.Column(db.String(50))
    type = db.Column(db.String(50))
    dataset = db.relationship("FoodDataset", back_populates="ds_meta_data", uselist=False)

    nutritional_values = db.relationship(
        "FoodNutritionalValue",
        back_populates="ds_meta_data",
        cascade="all, delete-orphan",
    )

    authors = db.relationship(
        "app.modules.basedataset.models.BaseAuthor",
        backref="food_ds_metadata",
        lazy=True,
        cascade="all, delete",
        foreign_keys="app.modules.basedataset.models.BaseAuthor.food_ds_meta_data_id",
    )

    __mapper_args__ = {
        "polymorphic_identity": "food_ds_meta_data",
    }


class FoodNutritionalValue(db.Model):
    __tablename__ = "food_nutritional_value"

    id = db.Column(db.Integer, primary_key=True)

    ds_meta_data_id = db.Column(
        db.Integer, db.ForeignKey("food_ds_meta_data.id", use_alter=True, name="fk_nutritional_val_ds_metadata")
    )

    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.String(50), nullable=False)

    ds_meta_data = db.relationship("FoodDSMetaData", back_populates="nutritional_values")

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }
