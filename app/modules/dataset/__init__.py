from flask import Blueprint

# Crear blueprint básico
dataset_bp = Blueprint('dataset', __name__, template_folder='templates')

def init_blueprint_api():
    """
    Función para inicializar la API del dataset
    Ahora esta función NO hace nada, ya que la API se maneja desde profile/routes.py
    """
    return None  # o puedes retornar dataset_bp si es necesario

# Importar routes al final para evitar dependencias circulares
from . import routes