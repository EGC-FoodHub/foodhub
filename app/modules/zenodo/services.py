import logging
import os

import requests
from dotenv import load_dotenv
from flask import jsonify

from app.modules.fooddataset.models import FoodDataset
from app.modules.foodmodel.models import FoodModel
from app.modules.zenodo.repositories import ZenodoRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)
load_dotenv()


class ZenodoService(BaseService):
    def __init__(self):
        super().__init__(ZenodoRepository())

        self.ZENODO_ACCESS_TOKEN = os.getenv("ZENODO_ACCESS_TOKEN")
        self.ZENODO_API_URL = self.get_zenodo_url()
        self.headers = {"Content-Type": "application/json"}
        self.params = {"access_token": self.ZENODO_ACCESS_TOKEN}

    def get_zenodo_url(self):
        FLASK_ENV = os.getenv("FLASK_ENV", "development")
        if FLASK_ENV == "production":
            return os.getenv("ZENODO_API_URL", "https://zenodo.org/api/deposit/depositions")
        return os.getenv("ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions")

    def create_new_deposition(self, dataset: FoodDataset) -> dict:
        """
        Crea una nueva deposición en Zenodo usando metadatos de FoodDataset.
        """
        logger.info("Dataset sending to Zenodo...")

        pub_type = "none"
        if hasattr(dataset.ds_meta_data, "publication_type"):
            pub_type = dataset.ds_meta_data.publication_type.value

        metadata = {
            "title": dataset.ds_meta_data.title,
            "upload_type": "dataset" if pub_type == "none" else "publication",
            "publication_type": pub_type if pub_type != "none" else None,
            "description": dataset.ds_meta_data.description,
            "creators": [
                {"name": author.name, "affiliation": author.affiliation or "", "orcid": author.orcid or ""}
                for author in dataset.ds_meta_data.authors
            ],
            "keywords": ["foodhub"] + (dataset.ds_meta_data.tags.split(", ") if dataset.ds_meta_data.tags else []),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

        response = requests.post(
            self.ZENODO_API_URL, params=self.params, json={"metadata": metadata}, headers=self.headers
        )
        if response.status_code != 201:
            raise Exception(f"Failed to create deposition: {response.json()}")
        return response.json()

    def upload_file(self, dataset: FoodDataset, deposition_id: int, food_model: FoodModel) -> dict:
        """
        Sube un archivo .food a Zenodo.
        """
        filename = food_model.food_meta_data.food_filename
        user_id = dataset.user_id

        file_path = os.path.join(uploads_folder_name(), f"user_{user_id}", f"dataset_{dataset.id}", filename)

        if not os.path.exists(file_path):
            raise Exception(f"File not found at {file_path}")

        files = {"file": open(file_path, "rb")}
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"

        response = requests.post(publish_url, params=self.params, data={"name": filename}, files=files)
        files["file"].close()

        if response.status_code != 201:
            raise Exception(f"Failed to upload file: {response.json()}")
        return response.json()

    def publish_deposition(self, deposition_id: int) -> dict:
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/actions/publish"
        response = requests.post(publish_url, params=self.params, headers=self.headers)
        if response.status_code != 202:
            raise Exception("Failed to publish deposition")
        return response.json()

    def get_deposition(self, deposition_id: int) -> dict:
        response = requests.get(f"{self.ZENODO_API_URL}/{deposition_id}", params=self.params, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to get deposition")
        return response.json()

    def get_doi(self, deposition_id: int) -> str:
        return self.get_deposition(deposition_id).get("doi")

    def test_connection(self) -> bool:
        response = requests.get(self.ZENODO_API_URL, params=self.params, headers=self.headers)
        return response.status_code == 200
