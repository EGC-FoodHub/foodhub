from datetime import datetime, timedelta

from sqlalchemy import and_, func

from app import db
from app.modules.basedataset.models import BaseDataset, BaseDSMetaData


class FoodDataset(BaseDataset):
    __tablename__ = "food_dataset"

    id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"), primary_key=True)

    ds_meta_data_id = db.Column(
        db.Integer, db.ForeignKey("food_ds_meta_data.id", use_alter=True, name="fk_food_dataset_ds_metadata")
    )

    view_count = db.Column(db.Integer, default=0, nullable=False)
    download_count = db.Column(db.Integer, default=0, nullable=False)
    last_viewed_at = db.Column(db.DateTime, nullable=True)
    last_downloaded_at = db.Column(db.DateTime, nullable=True)

    ds_meta_data = db.relationship(
        "FoodDSMetaData", back_populates="dataset", uselist=False, foreign_keys=[ds_meta_data_id]
    )

    files = db.relationship("FoodModel", back_populates="dataset", cascade="all, delete-orphan")

    activity_logs = db.relationship("FoodDatasetActivity", back_populates="dataset", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_identity": "food_dataset",
    }

    def __repr__(self):
        return f"<FoodDataset {self.id}>"

    def increment_view(self):
        self.view_count += 1
        self.last_viewed_at = datetime.now()

        activity = FoodDatasetActivity(dataset_id=self.id, activity_type="view", timestamp=datetime.now())
        db.session.add(activity)

    def increment_download(self):
        self.download_count += 1
        self.last_downloaded_at = datetime.now()

        activity = FoodDatasetActivity(dataset_id=self.id, activity_type="download", timestamp=datetime.now())
        db.session.add(activity)

    def get_recent_views(self, days=7):
        cutoff_date = datetime.now() - timedelta(days=days)
        return (
            db.session.query(func.count(FoodDatasetActivity.id))
            .filter(
                and_(
                    FoodDatasetActivity.dataset_id == self.id,
                    FoodDatasetActivity.activity_type == "view",
                    FoodDatasetActivity.timestamp >= cutoff_date,
                )
            )
            .scalar()
            or 0
        )

    def get_recent_downloads(self, days=7):
        cutoff_date = datetime.now() - timedelta(days=days)
        return (
            db.session.query(func.count(FoodDatasetActivity.id))
            .filter(
                and_(
                    FoodDatasetActivity.dataset_id == self.id,
                    FoodDatasetActivity.activity_type == "download",
                    FoodDatasetActivity.timestamp >= cutoff_date,
                )
            )
            .scalar()
            or 0
        )

    def calculate_trending_score(self, days=7, download_weight=2.0, view_weight=1.0):
        recent_downloads = self.get_recent_downloads(days)
        recent_views = self.get_recent_views(days)
        return (recent_downloads * download_weight) + (recent_views * view_weight)

    def get_main_author(self):
        if self.ds_meta_data and self.ds_meta_data.authors:
            main_author = self.ds_meta_data.authors[0]
            return {
                "name": main_author.name,
                "affiliation": main_author.affiliation,
                "orcid": main_author.orcid,
            }
        return None

    def to_trending_dict(self):
        return {
            "id": self.id,
            "title": self.ds_meta_data.title if self.ds_meta_data else "Sin título",
            "main_author": self.get_main_author(),
            "community": self.ds_meta_data.community if self.ds_meta_data else None,
            "download_count": self.download_count,
            "view_count": self.view_count,
            "recent_downloads_week": self.get_recent_downloads(7),
            "recent_views_week": self.get_recent_views(7),
            "recent_downloads_month": self.get_recent_downloads(30),
            "recent_views_month": self.get_recent_views(30),
            "trending_score": self.calculate_trending_score(),
            "last_downloaded_at": self.last_downloaded_at.isoformat() if self.last_downloaded_at else None,
            "last_viewed_at": self.last_viewed_at.isoformat() if self.last_viewed_at else None,
            "doi": self.ds_meta_data.dataset_doi if self.ds_meta_data else None,
        }

    @staticmethod
    def get_trending(period_days=7, limit=10):

        cutoff_date = datetime.now() - timedelta(days=period_days)

        downloads_subquery = (
            db.session.query(
                FoodDatasetActivity.dataset_id, func.count(FoodDatasetActivity.id).label("recent_downloads")
            )
            .filter(and_(FoodDatasetActivity.activity_type == "download", FoodDatasetActivity.timestamp >= cutoff_date))
            .group_by(FoodDatasetActivity.dataset_id)
            .subquery()
        )

        views_subquery = (
            db.session.query(FoodDatasetActivity.dataset_id, func.count(FoodDatasetActivity.id).label("recent_views"))
            .filter(and_(FoodDatasetActivity.activity_type == "view", FoodDatasetActivity.timestamp >= cutoff_date))
            .group_by(FoodDatasetActivity.dataset_id)
            .subquery()
        )

        trending_datasets = (
            db.session.query(FoodDataset)
            .outerjoin(downloads_subquery, FoodDataset.id == downloads_subquery.c.dataset_id)
            .outerjoin(views_subquery, FoodDataset.id == views_subquery.c.dataset_id)
            .order_by(
                (
                    func.coalesce(downloads_subquery.c.recent_downloads, 0) * 2
                    + func.coalesce(views_subquery.c.recent_views, 0)
                ).desc()
            )
            .limit(limit)
            .all()
        )

        return [dataset.to_trending_dict() for dataset in trending_datasets]


class FoodDSMetaData(BaseDSMetaData):
    __tablename__ = "food_ds_meta_data"

    id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"), primary_key=True)
    calories = db.Column(db.String(50))
    type = db.Column(db.String(50))

    community = db.Column(db.String(200), nullable=True)

    dataset = db.relationship("FoodDataset", back_populates="ds_meta_data", uselist=False)

    nutritional_values = db.relationship(
        "FoodNutritionalValue",
        back_populates="ds_meta_data",
        cascade="all, delete-orphan",
    )

    authors = db.relationship(
        "app.modules.basedataset.models.BaseAuthor",
        backref="food_ds_metadata",
        lazy=True,
        cascade="all, delete",
        foreign_keys="app.modules.basedataset.models.BaseAuthor.food_ds_meta_data_id",
    )

    __mapper_args__ = {
        "polymorphic_identity": "food_ds_meta_data",
    }


class FoodNutritionalValue(db.Model):
    __tablename__ = "food_nutritional_value"

    id = db.Column(db.Integer, primary_key=True)

    ds_meta_data_id = db.Column(
        db.Integer, db.ForeignKey("food_ds_meta_data.id", use_alter=True, name="fk_nutritional_val_ds_metadata")
    )

    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.String(50), nullable=False)

    ds_meta_data = db.relationship("FoodDSMetaData", back_populates="nutritional_values")

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }


class FoodDatasetActivity(db.Model):

    __tablename__ = "food_dataset_activity"

    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("food_dataset.id"), nullable=False, index=True)
    activity_type = db.Column(db.String(20), nullable=False, index=True)  
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)

    dataset = db.relationship("FoodDataset", back_populates="activity_logs")

    def __repr__(self):
        return f"<FoodDatasetActivity {self.activity_type} on dataset {self.dataset_id}>"
