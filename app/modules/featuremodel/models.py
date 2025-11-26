from sqlalchemy import Enum as SQLAlchemyEnum

from app import db
from app.modules.basedataset.models import BaseAuthor, BasePublicationType


class FeatureModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_set_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"), nullable=False)
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey("fm_meta_data.id"))
    files = db.relationship("Hubfile", back_populates="feature_model", cascade="all, delete-orphan")
    fm_meta_data = db.relationship("FMMetaData", uselist=False, backref="feature_model", cascade="all, delete")

    def __repr__(self):
        return f"FeatureModel<{self.id}>"


class FMMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uvl_filename = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(BasePublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    uvl_version = db.Column(db.String(120))
    fm_metrics_id = db.Column(db.Integer, db.ForeignKey("fm_metrics.id"))
    fm_metrics = db.relationship("FMMetrics", uselist=False, backref="fm_meta_data")
    authors = db.relationship(
        "BaseAuthor", backref="fm_metadata", lazy=True, cascade="all, delete", foreign_keys=[BaseAuthor.fm_meta_data_id]
    )

    def __repr__(self):
        return f"FMMetaData<{self.title}"


class FMMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solver = db.Column(db.Text)
    not_solver = db.Column(db.Text)

    def __repr__(self):
        return f"FMMetrics<solver={self.solver}, not_solver={self.not_solver}>"
