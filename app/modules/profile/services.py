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

            # Contar datasets subidos por el usuario
            from app.modules.dataset.models import DataSet
            uploaded_datasets_count = DataSet.query.filter_by(user_id=user_id).count()

            # Contar datasets sincronizados (con DOI) por el usuario
            from app.modules.dataset.models import DataSet, DSMetaData
            synchronized_datasets_count = (
                DataSet.query.join(DSMetaData)
                .filter(DataSet.user_id == user_id, DSMetaData.dataset_doi.isnot(None))
                .count()
            )

            metrics = {
                "uploaded_datasets": uploaded_datasets_count,
                "downloads": profile.downloaded_datasets_count,
                "synchronizations": synchronized_datasets_count,
            }

            return metrics, None

        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
