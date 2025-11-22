from abc import abstractmethod
from datetime import datetime
from enum import Enum

from requests import request
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
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"))
    food_meta_data_id = db.Column(db.Integer, db.ForeignKey("food_meta_data.id"))

    def to_dict(self):
        return {"name": self.name, "affiliation": self.affiliation, "orcid": self.orcid}


class BaseDSMetaData(db.Model):

    __abstract__ = True

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

    __abstract__ = True  # SQLAlchemy: evita crear tabla

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Discriminador de tipo; el server_default evita '' en inserts directos (problema del KeyError en mapper)
    basedataset_kind = db.Column(
        db.String(32),
        nullable=False,
        default="base",
        server_default="base",
        index=True,
    )

    __mapper_args__ = {
        "polymorphic_on": basedataset_kind,
    }

    @declared_attr
    def versions(cls):
        return db.relationship(
            "BaseDatasetVersion",
            back_populates="basedataset", # Asegúrate que en BaseDatasetVersion la relación inversa coincida
            lazy="dynamic",
            cascade="all, delete-orphan",
            order_by="BaseDatasetVersion.created_at.desc()",
        )

    @declared_attr
    def user(cls):
        return db.relationship("User", foreign_keys=[cls.user_id], back_populates="data_sets")

    # ---------------------
    # MÉTODOS ABSTRACTOS
    # (obligatorios)
    # ---------------------

    @abstractmethod
    def get_all_files(self):
        """
        Devuelve una lista con todos los archivos del dataset.
        UVLDataset -> recorrer FeatureModels
        FoodDataset -> recorrer documentos .food
        """
        pass

    @abstractmethod
    def parse_uploaded_file(self, file_storage):
        """
        Procesa el archivo subido (.uvl, .food, etc.)
        Debe crear los modelos internos correspondientes.
        """
        pass

    @abstractmethod
    def calculate_metrics(self):
        """
        Calcula y actualiza DSMetrics del dataset.
        UVL: number_of_models, number_of_features
        FOOD: number_of_recipes, number_of_ingredients (por ejemplo)
        """
        pass

    # ---------------------------
    # Métodos COMUNES (usados por plantillas y APIs)
    # ---------------------------
    def name(self) -> str:
        return self.ds_meta_data.title

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def _normalize_publication_type(self):
        """
        Devuelve un PublicationType o None, acepte lo que haya en ds_meta_data.publication_type.
        Puede venir como Enum, str (value o name), o None.
        """
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
        # Uso local para evitar import circular
        size = self.get_file_total_size()
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"
        return f"{round(size / (1024 ** 3), 2)} GB"

    def get_zenodo_url(self):
        return f"https://zenodo.org/record/{self.ds_meta_data.deposition_id}" if self.ds_meta_data.dataset_doi else None

    def get_doi(self):
        from app.modules.basedataset.services import BaseDatasetService

        return BaseDatasetService.get_doi(self)

    # def to_dict(self):
    #     return {
    #         "title": self.bds_meta_data.title,
    #         "id": self.id,
    #         "created_at": self.created_at,
    #         "created_at_timestamp": int(self.created_at.timestamp()),
    #         "description": self.bds_meta_data.description,
    #         "authors": [author.to_dict() for author in self.bds_meta_data.authors],
    #         "publication_type": self.get_cleaned_publication_type(),
    #         "publication_doi": self.bds_meta_data.publication_doi,
    #         "dataset_doi": self.bds_meta_data.dataset_doi,
    #         "tags": self.bds_meta_data.tags.split(",") if self.bds_meta_data.tags else [],
    #         "url": self.get_doi(),
    #         "download": f'{request.host_url.rstrip("/")}/basedataset/download/{self.id}',
    #         "zenodo": self.get_zenodo_url(),
    #         "files": self.files,
    #         "files_count": self.get_files_count(),
    #         "total_size_in_bytes": self.get_file_total_size(),
    #         "total_size_in_human_format": self.get_file_total_size_for_human(),
    #         "basedataset_kind": self.basedataset_kind,
    #         "specific_template": self.specific_template(),  # para vistas modulares
    #     }

    def get_latest_version(self):
        """Obtener la última versión del dataset"""
        return self.versions.first()

    def get_version_count(self):
        """Contar número de versiones"""
        return self.versions.count()

    # ---------------------------
    # HOOKS por tipo (cada subclase sobreescribe)
    # ---------------------------
    @classmethod
    def kind(cls) -> str:
        """Identificador de tipo (coincide con polymorphic_identity)."""
        return "base"

    def validate_upload(self, file_path: str) -> bool:
        """
        Validación de ficheros asociada al TIPO de dataset.
        Base: no valida nada. Subclases implementan su lógica.
        """
        return True

    def versioning_rules(self) -> dict:
        """
        Reglas de versionado para este tipo.
        Ejem: {"bump_on_new_file": True, "semantic": True}
        """
        return {}

    def specific_template(self) -> str | None:
        """
        Nombre de plantilla parcial específica para el detalle/explorer,
        por ejemplo: "dataset/blocks/food_preview.html".
        """
        return None

    def __repr__(self):
        return f"Basedataset<{self.id}>"


class BaseDatasetVersion(db.Model):

    __tablename__ = "basedataset_version"

    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"), nullable=False)
    version_number = db.Column(db.String(20), nullable=False)  # Formato: "1.0.0"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Snapshot de metadatos en esta versión
    title = db.Column(db.String(200))
    description = db.Column(db.Text)

    # Snapshot de archivos (JSON: {filename: {checksum, size, id}})
    files_snapshot = db.Column(db.JSON)

    # Mensaje de cambios (changelog)
    changelog = db.Column(db.Text)

    # Usuario que creó esta versión
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # Polimorfismo para extensiones específicas
    version_type = db.Column(db.String(50))

    __mapper_args__ = {"polymorphic_identity": "base", "polymorphic_on": version_type}

    # Relaciones
    dataset = db.relationship("BaseDataset", back_populates="versions")
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<DatasetVersion {self.version_number} for Dataset {self.dataset_id}>"

    def to_dict(self):
        """Serializar a diccionario"""
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
        """
        Comparar esta versión con otra.
        Método base que puede ser sobrescrito por subclases.
        """
        return {
            "metadata_changes": self._compare_metadata(other_version),
            "file_changes": self._compare_files(other_version),
        }

    def _compare_metadata(self, other):
        """Comparar cambios en metadatos"""
        changes = {}
        if self.title != other.title:
            changes["title"] = {"old": other.title, "new": self.title}
        if self.description != other.description:
            changes["description"] = {"old": other.description, "new": self.description}
        return changes

    def _compare_files(self, other):
        """Comparar cambios en archivos"""
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

    # ---------------------------


# Métricas/Registros/DOI mapping
# ---------------------------
class BaseDSDownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"))
    download_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    download_cookie = db.Column(db.String(36), nullable=False)  # UUID4

    def __repr__(self):
        return (
            f"<Download id={self.id} dataset_id={self.dataset_id} "
            f"date={self.download_date} cookie={self.download_cookie}>"
        )


class BaseDSViewRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"))
    view_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    view_cookie = db.Column(db.String(36), nullable=False)  # UUID4

    def __repr__(self):
        return f"<View id={self.id} dataset_id={self.dataset_id} date={self.view_date} cookie={self.view_cookie}>"


class BaseDOIMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_doi_old = db.Column(db.String(120))
    dataset_doi_new = db.Column(db.String(120))
