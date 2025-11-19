from core.resources.generic_resource import create_resource
from core.serialisers.serializer import Serializer


file_fields = {"file_id": "id", "file_name": "name", "size": "get_formatted_size"}
file_serializer = Serializer(file_fields)

basedataset_fields = {
    "dataset_id": "id",
    "created": "created_at",
    "name": "name",
    "doi": "get_doi",
    "files": "files",
}

basedataset_serializer = Serializer(basedataset_fields, related_serializers={"files": file_serializer})

# TODO: Replace None with BaseDataSet model when it is created
BaseDataSetResource = create_resource(None, basedataset_serializer)

def init_blueprint_api(api):
    """Function to register resources with the provided Flask-RESTful Api instance."""
    api.add_resource(BaseDataSetResource, "/api/v1/basedatasets/", endpoint="basedatasets")
    api.add_resource(BaseDataSetResource, "/api/v1/basedatasets/<int:id>", endpoint="basedataset")