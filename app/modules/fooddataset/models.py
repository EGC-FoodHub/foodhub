import enum

import yaml  # Lo he movido arriba para que esté limpio

from app import db
from app.modules.basedataset.models import BaseDataset, BaseDSMetaData
from app.modules.foodmodel.models import FoodMetaData, FoodModel

# ======================================================
#   ENUM: Tipo de alimento
# ======================================================


class FoodType(enum.Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    ANIMAL = "animal"
    MIXED = "mixed"
    OTHER = "other"


# ======================================================
#   FOOD DATASET
#   (solo la parte administrativa / contenedor)
# ======================================================


class FoodDataset(BaseDataset):

    __tablename__ = "food_dataset"

    id = db.Column(db.Integer, db.ForeignKey("data_set.id"), primary_key=True)

    # CAMBIO 1: Renombrar metadata_id y la relación metadata
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("food_ds_meta_data.id"))

    # ¡AQUÍ ESTABA EL ERROR! "metadata" es reservado. Lo llamamos "ds_meta_data"
    ds_meta_data = db.relationship("FoodDSMetaData", back_populates="dataset")

    # Archivos .food asociados
    files = db.relationship(
        "FoodFile",
        back_populates="dataset",
        cascade="all, delete-orphan",
        lazy=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "food",
    }

    # --------------------------------------------------------
    # IMPLEMENTACIÓN DE MÉTODOS ABSTRACTOS
    # --------------------------------------------------------

    def get_all_files(self):
        return self.files

    def parse_uploaded_file(self, file_storage):
        """
        Procesa un archivo .food subido por el usuario.
        """
        # -------------------------------
        # 1. Leer archivo
        # -------------------------------
        raw_content = file_storage.read().decode("utf-8")
        data = yaml.safe_load(raw_content)

        # -------------------------------
        # 2. Crear metadatos del alimento
        # -------------------------------
        meta = FoodMetaData(
            food_filename=file_storage.filename,
            name=data.get("name", "Unnamed Food Item"),
            food_type=data.get("type", "UNKNOWN"),
            calories=data.get("calories"),
            original_content=raw_content,
        )

        # -------------------------------
        # 3. Nutritional values
        # -------------------------------
        nutritional_data = data.get("nutritional_values", {})

        meta.nutritional_values = FoodNutritionalValue(
            protein=nutritional_data.get("protein"),
            carbohydrates=nutritional_data.get("carbohydrates"),
            fat=nutritional_data.get("fat"),
            fiber=nutritional_data.get("fiber"),
            vitamin_e=nutritional_data.get("vitamin_e"),
            magnesium=nutritional_data.get("magnesium"),
            calcium=nutritional_data.get("calcium"),
        )

        # -------------------------------
        # 4. Crear FoodModel asociado al dataset
        # -------------------------------
        food_model = FoodModel(
            data_set_id=self.id,
            food_meta_data=meta,
        )

        db.session.add(food_model)

        return food_model

    def calculate_metrics(self):
        """
        Calcula métricas simples.
        """
        # CAMBIO 2: Usar self.ds_meta_data en lugar de self.metadata
        if not self.ds_meta_data or not self.files:
            return

        # Ejemplo simple de métrica
        self.ds_meta_data.number_of_files = len(self.files)

        try:
            # "579 kcal" -> 579
            calories_str = str(self.ds_meta_data.calories).split()[0]
            self.ds_meta_data.total_calories = int(calories_str)
        except:
            self.ds_meta_data.total_calories = None

        db.session.commit()


# ======================================================
#   FOOD METADATA
#   (contenido científico derivado del .food file)
# ======================================================


class FoodDSMetaData(BaseDSMetaData):
    __tablename__ = "food_ds_meta_data"

    calories = db.Column(db.String(50))
    type = db.Column(db.String(50))

    # CAMBIO 3: Actualizar back_populates a "ds_meta_data"
    nutritional_values = db.relationship(
        "FoodNutritionalValue",
        back_populates="ds_meta_data",  # Coincide con el nombre en FoodNutritionalValue
        cascade="all, delete-orphan",
    )

    # CAMBIO 4: Actualizar back_populates a "ds_meta_data"
    dataset = db.relationship("FoodDataset", back_populates="ds_meta_data", uselist=False)


# ======================================================
#   FOOD NUTRITIONAL VALUES
#   (tabla dinámica para vitaminas, proteínas, etc)
# ======================================================


class FoodNutritionalValue(db.Model):
    __tablename__ = "food_nutritional_value"

    id = db.Column(db.Integer, primary_key=True)

    # CAMBIO 5: Renombrar la FK y la relación
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("food_ds_meta_data.id"))

    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.String(50), nullable=False)

    # CAMBIO 6: Renombrar la relación de metadata -> ds_meta_data
    ds_meta_data = db.relationship("FoodDSMetaData", back_populates="nutritional_values")

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }
