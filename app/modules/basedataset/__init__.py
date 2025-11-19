from flask_restful import Api
from core.blueprints.base_blueprint import BaseBlueprint
from app.modules.basedataset.api import init_blueprint_api

basedataset_bp = BaseBlueprint('basedataset', __name__, template_folder='templates')

api = Api(basedataset_bp)
init_blueprint_api(api)