from app.modules.basedataset.models import BaseDataset
from core.resources.generic_resource import create_resource
from core.serialisers.serializer import Serializer

meta_fields = {
    "title": "title",
    "description": "description",
    "publication_type": "publication_type",
    "dataset_doi": "dataset_doi",
    "publication_doi": "publication_doi",
    "tags": "tags",
}
meta_serializer = Serializer(meta_fields)
basedataset_fields = {"id": "id", "created_at": "created_at", "user_id": "user_id", "metadata": "ds_meta_data"}

basedataset_serializer = Serializer(basedataset_fields, related_serializers={"metadata": meta_serializer})

BaseDataSetResource = create_resource(BaseDataset, basedataset_serializer)


def init_blueprint_api(api):
    """Function to register resources with the provided Flask-RESTful Api instance."""
    api.add_resource(BaseDataSetResource, "/api/v1/datasets/", endpoint="datasets")
    api.add_resource(BaseDataSetResource, "/api/v1/datasets/<int:id>", endpoint="dataset")
