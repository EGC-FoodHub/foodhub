from flask_restful import Api

from app.modules.Basedataset.api import init_blueprint_api
from core.blueprints.base_blueprint import BaseBlueprint

dataset_bp = BaseBlueprint("basedataset", __name__, template_folder="templates")


api = Api(dataset_bp)
init_blueprint_api(api)
