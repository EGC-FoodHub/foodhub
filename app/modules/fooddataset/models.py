import enum
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

    # Relación con metadatos específicos
    metadata_id = db.Column(db.Integer, db.ForeignKey("food_ds_metadata.id"))
    metadata = db.relationship("FoodDSMetaData", back_populates="dataset")

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
        """
        Devuelve todos los archivos .food del dataset.
        """
        return self.files

    def parse_uploaded_file(self, file_storage):
        """
        Procesa un archivo .food subido por el usuario.
        - Lee y parsea el archivo YAML
        - Crea FoodMetaData
        - Crea FoodNutritionalValue
        - Crea FoodModel dentro del FoodDataset
        """
        import yaml

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

        # Persistencia
        from app import db
        db.session.add(food_model)

        return food_model


    def calculate_metrics(self):
        """
        Calcula métricas simples:
        - number_of_files
        - total_calories (sumatorio si hubiera varios archivos)
        """
        if not self.metadata or not self.files:
            return

        # Ejemplo simple de métrica
        self.metadata.number_of_files = len(self.files)

        # Si tuvieras más modelos asociados podrías calcular más cosas
        # Pero como es alimentación, puedes añadir:
        try:
            # "579 kcal" -> 579
            calories_str = str(self.metadata.calories).split()[0]
            self.metadata.total_calories = int(calories_str)
        except:
            self.metadata.total_calories = None

        db.session.commit()


# ======================================================
#   FOOD METADATA
#   (contenido científico derivado del .food file)
# ======================================================

class FoodDSMetaData(BaseDSMetaData):
    """
    Representa los metadatos científicos del archivo .food:
    - Nombre
    - Calorías
    - Tipo
    - Valores nutricionales
    """

    __tablename__ = "food_ds_meta_data"

    # Ejemplo de campos extra provenientes del archivo .food
    calories = db.Column(db.String(50))
    type = db.Column(db.String(50))

    # Relación con tabla de valores nutricionales
    nutritional_values = db.relationship(
        "FoodNutritionalValue",
        back_populates="metadata",
        cascade="all, delete-orphan"
    )

    # Relación 1–1 con el dataset FoodDataset
    dataset = db.relationship(
        "FoodDataset",
        back_populates="metadata",
        uselist=False
    )

    


# ======================================================
#   FOOD NUTRITIONAL VALUES
#   (tabla dinámica para vitaminas, proteínas, etc)
# ======================================================

class FoodNutritionalValue(db.Model):
    """
    Representa un valor nutricional dinámico:
    Ejemplos:
    - protein: 21g
    - vitamin_e: 131%
    - magnesium: 67%
    """

    __tablename__ = "food_nutritional_value"

    id = db.Column(db.Integer, primary_key=True)
    metadata_id = db.Column(db.Integer, db.ForeignKey("food_ds_meta_data.id"))

    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.String(50), nullable=False)

    metadata = db.relationship(
        "FoodDSMetaData",
        back_populates="nutritional_values"
    )

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }
