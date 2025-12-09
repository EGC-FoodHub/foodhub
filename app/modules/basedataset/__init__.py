from flask_restful import Api

from app.modules.basedataset.api import init_blueprint_api
from core.blueprints.base_blueprint import BaseBlueprint

basedataset_bp = BaseBlueprint("basedataset", __name__, template_folder="templates")

api = Api(basedataset_bp)
init_blueprint_api(api)
