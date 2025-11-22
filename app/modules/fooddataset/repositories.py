from app import db
from app.modules.basedataset.repositories import BaseDatasetRepository
from app.modules.hubfile.models import Hubfile

from .models import FoodDataset, FoodDSMetaData, FoodNutritionalValue


class FoodDatasetRepository(BaseDatasetRepository):
    """
    Repositorio específico para datasets FOOD.
    Hereda de BaseDatasetRepository para operaciones CRUD estándar.
    """

    model = FoodDataset

    # ------------------------------------------------------------
    # ESPECÍFICOS FOOD
    # ------------------------------------------------------------

    def get_by_metadata_id(self, metadata_id: int) -> FoodDataset | None:
        return self.model.query.filter_by(metadata_id=metadata_id).first()

    def get_all_food_datasets(self):
        """Devuelve únicamente datasets de tipo FOOD."""
        return self.model.query.all()

    def get_nutritional_values(self, dataset_id: int) -> FoodNutritionalValue | None:
        dataset = self.get(dataset_id)
        if not dataset or not dataset.metadata:
            return None
        return dataset.metadata.nutritional_values

    def get_files(self, dataset_id: int):
        dataset = self.get(dataset_id)
        if not dataset:
            return []
        return dataset.hubfiles.all()

    # ------------------------------------------------------------
    # OPERACIONES DE CREACIÓN Y ACTUALIZACIÓN
    # ------------------------------------------------------------

    def attach_metadata(self, dataset: FoodDataset, metadata: FoodDSMetaData):
        dataset.metadata = metadata
        db.session.add(dataset)
        return dataset

    def create_metadata(
        self,
        title: str,
        food_type: str,
        description: str = "",
        nutritional_values: dict | None = None,
    ) -> FoodDSMetaData:

        meta = FoodDSMetaData(title=title, food_type=food_type, description=description)

        db.session.add(meta)
        db.session.flush()  # para obtener meta.id

        # Crear valores nutricionales
        if nutritional_values:
            nutrition = FoodNutritionalValue(metadata_id=meta.id, **nutritional_values)
            db.session.add(nutrition)

        return meta

    def add_file(self, dataset: FoodDataset, name: str, checksum: str, size: int, content_path: str):
        file = Hubfile(name=name, checksum=checksum, size=size, dataset=dataset)
        db.session.add(file)
        return file

    # ------------------------------------------------------------
    # BORRADO
    # ------------------------------------------------------------

    def delete_dataset(self, dataset_id: int):
        dataset = self.get(dataset_id)
        if not dataset:
            return False

        db.session.delete(dataset)
        return True
