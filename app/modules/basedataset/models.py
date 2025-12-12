from abc import abstractmethod
from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.ext.declarative import declared_attr

from app import db


class BasePublicationType(Enum):
    NONE = "none"
    ANNOTATION_COLLECTION = "annotationcollection"
    BOOK = "book"
    BOOK_SECTION = "section"
    CONFERENCE_PAPER = "conferencepaper"
    DATA_MANAGEMENT_PLAN = "datamanagementplan"
    JOURNAL_ARTICLE = "article"
    PATENT = "patent"
    PREPRINT = "preprint"
    PROJECT_DELIVERABLE = "deliverable"
    PROJECT_MILESTONE = "milestone"
    PROPOSAL = "proposal"
    REPORT = "report"
    SOFTWARE_DOCUMENTATION = "softwaredocumentation"
    TAXONOMIC_TREATMENT = "taxonomictreatment"
    TECHNICAL_NOTE = "technicalnote"
    THESIS = "thesis"
    WORKING_PAPER = "workingpaper"
    OTHER = "other"


class BaseAuthor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    affiliation = db.Column(db.String(120))
    orcid = db.Column(db.String(120))
    food_meta_data_id = db.Column(
        db.Integer, db.ForeignKey("food_meta_data.id", use_alter=True, name="fk_author_food_metadata")
    )
    food_ds_meta_data_id = db.Column(
        db.Integer, db.ForeignKey("food_ds_meta_data.id", use_alter=True, name="fk_author_food_ds_metadata")
    )
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"))

    def to_dict(self):
        return {"name": self.name, "affiliation": self.affiliation, "orcid": self.orcid}


class BaseDSMetaData(db.Model):
    __tablename__ = "ds_meta_data"

    id = db.Column(db.Integer, primary_key=True)
    deposition_id = db.Column(db.Integer)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(BasePublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))

    @declared_attr
    def authors(cls):
        return db.relationship("BaseAuthor", backref="ds_meta_data", lazy=True, cascade="all, delete")


class BaseDataset(db.Model):
    __tablename__ = "base_dataset"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    basedataset_kind = db.Column(
        db.String(32),
        nullable=False,
        default="base",
        server_default="base",
        index=True,
    )

    __mapper_args__ = {"polymorphic_on": basedataset_kind, "polymorphic_identity": "base"}
    versions = db.relationship(
        "app.modules.basedataset.models.BaseDatasetVersion",
        back_populates="dataset",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="BaseDatasetVersion.created_at.desc()",
    )
    user = db.relationship("app.modules.auth.models.User", foreign_keys=[user_id], back_populates="data_sets")

    @abstractmethod
    def get_all_files(self):
        pass

    @abstractmethod
    def parse_uploaded_file(self, file_storage):
        pass

    @abstractmethod
    def calculate_metrics(self):
        pass

    def name(self) -> str:
        return self.ds_meta_data.title if hasattr(self, "ds_meta_data") else "Untitled"

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def _normalize_publication_type(self):
        if not hasattr(self, "ds_meta_data") or not self.ds_meta_data:
            return None
        pt = getattr(self.ds_meta_data, "publication_type", None)
        if pt is None:
            return None
        if isinstance(pt, BasePublicationType):
            return pt
        s = str(pt).strip()
        for enum_member in BasePublicationType:
            if enum_member.value == s:
                return enum_member
        for enum_member in BasePublicationType:
            if enum_member.name == s:
                return enum_member
        return None

    def get_cleaned_publication_type(self) -> str:
        pt = self._normalize_publication_type()
        if not pt:
            return "None"
        return pt.name.replace("_", " ").title()

    def get_files_count(self) -> int:
        return len(self.files)

    def get_file_total_size(self) -> int:
        total_size = 0
        for file in self.files:
            total_size += file.size_in_bytes
        return total_size

    def get_file_total_size_for_human(self) -> str:
        size = self.get_file_total_size()
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"
        return f"{round(size / (1024 ** 3), 2)} GB"

    def get_zenodo_url(self):
        return (
            f"https://zenodo.org/record/{self.ds_meta_data.deposition_id}"
            if hasattr(self, "ds_meta_data") and self.ds_meta_data and self.ds_meta_data.dataset_doi
            else None
        )

    def to_dict(self):
        """Serializa el FoodDataset a un diccionario para JSON."""
        return {
            "id": self.id,
            "url": f"/dataset/view/{self.id}",
            "title": self.ds_meta_data.title if self.ds_meta_data else "Untitled",
            "publication_type": self.get_cleaned_publication_type(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "description": self.ds_meta_data.description if self.ds_meta_data else "",
            "authors": [author.to_dict() for author in self.ds_meta_data.authors] if self.ds_meta_data else [],
            "tags": self.ds_meta_data.tags.split(", ") if self.ds_meta_data and self.ds_meta_data.tags else [],
            "total_size_in_human_format": self.get_file_total_size_for_human(),
        }

    def get_doi(self):
        from app.modules.basedataset.services import BaseDatasetService

        return BaseDatasetService.get_doi(self)

    def get_latest_version(self):
        return self.versions.first()

    def get_version_count(self):
        return self.versions.count()

    @classmethod
    def kind(cls) -> str:
        return "base"

    def validate_upload(self, file_path: str) -> bool:
        return True

    def versioning_rules(self) -> dict:
        return {}

    def specific_template(self) -> str | None:
        return None

    def __repr__(self):
        return f"Basedataset<{self.id}>"


class BaseDatasetVersion(db.Model):

    __tablename__ = "basedataset_version"

    id = db.Column(db.Integer, primary_key=True)

    dataset_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"), nullable=False)

    version_number = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    files_snapshot = db.Column(db.JSON)
    changelog = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    version_type = db.Column(db.String(50))

    __mapper_args__ = {"polymorphic_identity": "base", "polymorphic_on": version_type}

    dataset = db.relationship("app.modules.basedataset.models.BaseDataset", back_populates="versions")

    created_by = db.relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<DatasetVersion {self.version_number} for Dataset {self.dataset_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "changelog": self.changelog,
            "created_by": self.created_by.profile.name if self.created_by else None,
            "title": self.title,
            "description": self.description,
        }

    def compare_with(self, other_version):
        return {
            "metadata_changes": self._compare_metadata(other_version),
            "file_changes": self._compare_files(other_version),
        }

    def _compare_metadata(self, other):
        changes = {}
        if self.title != other.title:
            changes["title"] = {"old": other.title, "new": self.title}
        if self.description != other.description:
            changes["description"] = {"old": other.description, "new": self.description}
        return changes

    def _compare_files(self, other):
        old_files = other.files_snapshot or {}
        new_files = self.files_snapshot or {}
        old_names = set(old_files.keys())
        new_names = set(new_files.keys())
        added = list(new_names - old_names)
        removed = list(old_names - new_names)
        modified = []
        for filename in old_names & new_names:
            if old_files[filename].get("checksum") != new_files[filename].get("checksum"):
                modified.append(filename)
        return {"added": added, "removed": removed, "modified": modified}


class BaseDSDownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"))
    download_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    download_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return f"<Download id={self.id} dataset_id={self.dataset_id}>"


class BaseDSViewRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"))
    view_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    view_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return f"<View id={self.id} dataset_id={self.dataset_id}>"


class BaseDSMetrics(db.Model):
    __tablename__ = "ds_metrics"

    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"))

    number_of_models = db.Column(db.String(100))

    def __repr__(self):
        return f"DSMetrics<dataset_id={self.dataset_id}>"


class BaseDOIMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_doi_old = db.Column(db.String(120))
    dataset_doi_new = db.Column(db.String(120))
