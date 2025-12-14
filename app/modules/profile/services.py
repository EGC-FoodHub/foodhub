from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.services.BaseService import BaseService


class UserProfileService(BaseService):
    def __init__(self):
        super().__init__(UserProfileRepository())

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

    def get_user_metrics(self, user_id: int):
        try:
            profile = UserProfile.query.filter_by(user_id=user_id).first()

            if not profile:
                return None, "User profile not found."

            from app.modules.basedataset.models import BaseDataset

            uploaded_datasets_count = BaseDataset.query.filter_by(user_id=user_id).count()

            # Contar datasets sincronizados (con DOI) por el usuario
            # Algunos subtipos de dataset (por ejemplo FoodDataset) almacenan metadata en tablas
            # específicas; para evitar imports frágiles, obtenemos los datasets del usuario
            # y contamos aquellos cuya metadata (`ds_meta_data.dataset_doi`) no sea None.
            user_datasets = BaseDataset.query.filter_by(user_id=user_id).all()
            synchronized_datasets_count = 0
            for ds in user_datasets:
                ds_meta = getattr(ds, "ds_meta_data", None)
                if ds_meta and getattr(ds_meta, "dataset_doi", None):
                    synchronized_datasets_count += 1

            # Contar descargas hechas por el usuario autenticado
            from app.modules.basedataset.models import BaseDSDownloadRecord

            downloads_count = BaseDSDownloadRecord.query.filter_by(user_id=user_id).count()

            metrics = {
                "uploaded_datasets": uploaded_datasets_count,
                "downloads": downloads_count,
                "synchronizations": synchronized_datasets_count,
            }

            return metrics, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
