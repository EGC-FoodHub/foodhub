from core.blueprints.base_blueprint import BaseBlueprint

food_checker_bp = BaseBlueprint("food_checker", __name__, template_folder="templates", url_prefix="/api/food_checker")
