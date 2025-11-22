import yaml
import hashlib

from app import db
from app.modules.basedataset.services import BaseDatasetService
from app.modules.fooddataset.repositories import FoodDatasetRepository
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData, FoodNutritionalValue
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.services import HubfileService


class FoodDatasetService(BaseDatasetService):
    """
    Servicio específico para FoodDataset.
    Extiende el comportamiento genérico de BaseDatasetService
    con lógica propia para procesar archivos .food.
    """

    def __init__(self):
        super().__init__()
        self.repo = FoodDatasetRepository()      # Reemplaza el repo genérico
        self.hubfile_service = HubfileService()

    # -------------------------------------------------------------------------
    # CREACIÓN ESPECÍFICA
    # -------------------------------------------------------------------------

    def create_food_dataset(self, user, name: str) -> FoodDataset:
        """
        Crea un dataset Food vacío. No crea archivos ni metadata aún.
        """
        dataset = self.repo.create(
            name=name,
            owner_user_id=user.id,
            dataset_type="FOOD"
        )
        return dataset

    # -------------------------------------------------------------------------
    # PARSEADOR DE ARCHIVOS .FOOD
    # -------------------------------------------------------------------------

    def parse_uploaded_file(self, dataset: FoodDataset, file_storage):
        """
        Procesa un archivo YAML .food, crea metadatos, valores nutricionales
        y guarda el archivo mediante Hubfile.
        """

        # 1) Leer archivo
        raw_content = file_storage.read().decode("utf-8")
        data = yaml.safe_load(raw_content)

        # 2) Crear metadatos
        metadata = FoodDSMetaData(
            title=data.get("name", "Unnamed Food"),
            description=data.get("description", f"Nutritional profile for {data.get('name')}"),
            food_type=data.get("type", "UNKNOWN"),
        )
        db.session.add(metadata)
        db.session.flush()    # obtiene metadata.id

        # 3) Crear valores nutricionales
        nv = data.get("nutritional_values", {})
        nutritional = FoodNutritionalValue(
            metadata_id=metadata.id,
            protein=nv.get("protein"),
            carbohydrates=nv.get("carbohydrates"),
            fat=nv.get("fat"),
            fiber=nv.get("fiber"),
            vitamin_e=nv.get("vitamin_e"),
            magnesium=nv.get("magnesium"),
            calcium=nv.get("calcium"),
        )
        db.session.add(nutritional)

        # 4) Asociar metadata al dataset
        dataset.metadata_id = metadata.id
        db.session.add(dataset)

        # 5) Guardar archivo como Hubfile
        checksum = hashlib.md5(raw_content.encode("utf-8")).hexdigest()

        hubfile = Hubfile(
            name=file_storage.filename,
            size=len(raw_content.encode("utf-8")),
            checksum=checksum,
            dataset=dataset
        )
        db.session.add(hubfile)

        db.session.commit()

        return hubfile

    # -------------------------------------------------------------------------
    # GETTERS
    # -------------------------------------------------------------------------

    def get_metadata(self, dataset_id: int):
        dataset = self.repo.get(dataset_id)
        return dataset.metadata if dataset else None

    def get_nutritional_values(self, dataset_id: int):
        return self.repo.get_nutritional_values(dataset_id)

    def get_files(self, dataset_id: int):
        return self.repo.get_files(dataset_id)

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------

    def delete_dataset(self, dataset_id: int) -> bool:
        ok = self.repo.delete_dataset(dataset_id)
        db.session.commit()
        return ok
