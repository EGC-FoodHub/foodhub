from sqlalchemy import event

from app.modules.fooddataset.models import FoodDataset
from core.services.SearchService import SearchService


def register_events():
    search_service = SearchService()

    if not search_service.enabled:
        return

    @event.listens_for(FoodDataset, "after_insert")
    def after_insert(mapper, connection, target):
        """Cuando se crea un dataset, indexarlo en Elastic."""
        try:
            search_service.index_dataset(target)
        except Exception as e:
            print(f"Error indexing dataset: {e}")

    @event.listens_for(FoodDataset, "after_update")
    def after_update(mapper, connection, target):
        """Si se edita, re-indexar."""
        try:
            search_service.index_dataset(target)
        except Exception:
            pass

    @event.listens_for(FoodDataset, "after_delete")
    def after_delete(mapper, connection, target):
        """Si se borra, quitar del índice."""
        try:
            search_service.delete_dataset(target.id)
        except Exception:
            pass
