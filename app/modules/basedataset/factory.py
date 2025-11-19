"""
DatasetFactory
--------------
Punto central del sistema modular de datasets.
Permite registrar nuevos tipos de dataset sin modificar rutas ni lógica interna.
"""

from typing import Dict, List, Type

from app.modules.basedataset.services import BaseDatasetService


class DatasetFactory:
    """
    Fábrica de servicios de datasets.
    Mantiene un registro de servicios especializados y extensiones permitidas.
    """

    # Registro: dataset_type -> servicio especializado
    _registered_services: Dict[str, BaseDatasetService] = {}

    # Extensiones aceptadas por todos los datasets
    _allowed_extensions: List[str] = []

    @classmethod
    def register_service(cls, dataset_type: str, service: BaseDatasetService, extensions: List[str]):
        """
        Registra un nuevo tipo de dataset en el sistema modular.

        :param dataset_type: String que identifica el tipo (ej: "UVL", "FOOD")
        :param service: Instancia del servicio especializado
        :param extensions: Lista de extensiones aceptadas por este dataset
        """
        dataset_type = dataset_type.upper()

        cls._registered_services[dataset_type] = service

        for ext in extensions:
            ext_lower = ext.lower()
            if ext_lower not in cls._allowed_extensions:
                cls._allowed_extensions.append(ext_lower)

    @classmethod
    def get_service(cls, dataset_type: str) -> BaseDatasetService:
        """
        Devuelve el servicio especializado correspondiente al tipo.
        Si no existe, devuelve el servicio base.
        """
        if not dataset_type:
            return BaseDatasetService()

        dataset_type = dataset_type.upper()

        return cls._registered_services.get(dataset_type, BaseDatasetService())

    @classmethod
    def allowed_extensions(cls) -> List[str]:
        """
        Devuelve todas las extensiones permitidas del sistema.
        """
        return cls._allowed_extensions
