from datetime import datetime
from enum import Enum

from flask import request
from sqlalchemy import Enum as SQLAlchemyEnum

from app.modules.dataset.handlers.food_handler import FoodHandler

from app import db


class PublicationType(Enum):
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


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    affiliation = db.Column(db.String(120))
    orcid = db.Column(db.String(120))
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"))
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey("fm_meta_data.id"))

    def to_dict(self):
        return {"name": self.name, "affiliation": self.affiliation, "orcid": self.orcid}


class DSMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number_of_models = db.Column(db.String(120))
    number_of_features = db.Column(db.String(120))

    def __repr__(self):
        return f"DSMetrics<models={self.number_of_models}, features={self.number_of_features}>"


class DSMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deposition_id = db.Column(db.Integer)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(PublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    ds_metrics_id = db.Column(db.Integer, db.ForeignKey("ds_metrics.id"))
    ds_metrics = db.relationship("DSMetrics", uselist=False, backref="ds_meta_data", cascade="all, delete")
    authors = db.relationship("Author", backref="ds_meta_data", lazy=True, cascade="all, delete")


class BaseDataset(db.Model):
    """
    Base polimórfica para todos los tipos de dataset (UVL, GPX, Image, Tabular, ...).
    Compartimos una sola tabla 'data_set' para compatibilidad con la plataforma.
    """

    __tablename__ = "data_set"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Discriminador de tipo; el server_default evita '' en inserts directos (problema del KeyError en mapper)
    dataset_kind = db.Column(
        db.String(32),
        nullable=False,
        default="base",
        server_default="base",
        index=True,
    )

    __mapper_args__ = {
        "polymorphic_on": dataset_kind,
    }
    versions = db.relationship(
        "DatasetVersion",
        back_populates="dataset",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="DatasetVersion.created_at.desc()",
    )
    user = db.relationship("User", foreign_keys=[user_id], back_populates="data_sets")
    ds_meta_data = db.relationship("DSMetaData", backref=db.backref("data_set", uselist=False))
    feature_models = db.relationship("FeatureModel", backref="data_set", lazy=True, cascade="all, delete")

    # ---------------------------
    # Métodos COMUNES (usados por plantillas y APIs)
    # ---------------------------
    def name(self) -> str:
        return self.ds_meta_data.title

    def files(self):
        return [file for fm in self.feature_models for file in fm.files]

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
        if isinstance(pt, PublicationType):
            return pt
        # Si llega como string, intentamos casar primero por value, luego por name
        s = str(pt).strip()
        for enum_member in PublicationType:
            if enum_member.value == s:
                return enum_member
        for enum_member in PublicationType:
            if enum_member.name == s:
                return enum_member
        return None

    def get_cleaned_publication_type(self) -> str:
        pt = self._normalize_publication_type()
        if not pt:
            return "None"
        # Mostrar bonito
        return pt.name.replace("_", " ").title()

    def get_files_count(self) -> int:
        return sum(len(fm.files) for fm in self.feature_models)

    def get_file_total_size(self) -> int:
        return sum((file.size or 0) for fm in self.feature_models for file in fm.files)

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

    def get_uvlhub_doi(self):
        # evitamos import circular; el servicio construye la URL pública
        from app.modules.dataset.services import DataSetService

        return DataSetService().get_uvlhub_doi(self)

    def to_dict(self):
        return {
            "title": self.ds_meta_data.title,
            "id": self.id,
            "created_at": self.created_at,
            "created_at_timestamp": int(self.created_at.timestamp()),
            "description": self.ds_meta_data.description,
            "authors": [author.to_dict() for author in self.ds_meta_data.authors],
            "publication_type": self.get_cleaned_publication_type(),
            "publication_doi": self.ds_meta_data.publication_doi,
            "dataset_doi": self.ds_meta_data.dataset_doi,
            "tags": self.ds_meta_data.tags.split(",") if self.ds_meta_data.tags else [],
            "url": self.get_uvlhub_doi(),
            "download": f'{request.host_url.rstrip("/")}/dataset/download/{self.id}',
            "zenodo": self.get_zenodo_url(),
            "files": [file.to_dict() for fm in self.feature_models for file in fm.files],
            "files_count": self.get_files_count(),
            "total_size_in_bytes": self.get_file_total_size(),
            "total_size_in_human_format": self.get_file_total_size_for_human(),
            "dataset_kind": self.dataset_kind,
            "specific_template": self.specific_template(),  # para vistas modulares
        }

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
        por ejemplo: "dataset/blocks/gpx_preview.html".
        """
        return None

    def __repr__(self):
        return f"Dataset<{self.id}:{self.dataset_kind}>"


class DatasetVersion(db.Model):
    """Modelo genérico para versiones de cualquier tipo de dataset"""

    __tablename__ = "dataset_version"

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


# ==========================================================
#   FOOD Dataset y versiones
# ==========================================================


class FoodDataset(BaseDataset):
    __mapper_args__ = {"polymorphic_identity": "food"}

    @classmethod
    def kind(cls) -> str:
        return "food"

    def validate_upload(self, file_path: str) -> bool:
        """Valida que el archivo subido sea de tipo .food"""
        return file_path.lower().endswith(".food")

    def specific_template(self) -> str | None:
        return "dataset/blocks/food_preview.html"

    def calculate_total_foods(self):
        """Cuenta todos los alimentos de todos los archivos .food"""
        handler = FoodHandler()
        summary = handler.summarize_dataset(self)
        return summary["total_foods"]

    def calculate_total_calories(self):
        """Calcula el total de calorías de todos los alimentos"""
        handler = FoodHandler()
        summary = handler.summarize_dataset(self)
        return summary["total_calories"]

    def calculate_average_calories(self):
        """Calcula el promedio de calorías por alimento"""
        handler = FoodHandler()
        summary = handler.summarize_dataset(self)
        return summary["average_calories"]

    def get_type_distribution(self):
        """Obtiene la distribución de alimentos por tipo"""
        handler = FoodHandler()
        summary = handler.summarize_dataset(self)
        return summary["type_distribution"]

    def get_nutritional_averages(self):
        """Obtiene los promedios nutricionales de todos los alimentos"""
        handler = FoodHandler()
        summary = handler.summarize_dataset(self)
        return summary["nutritional_averages"]

    def get_all_foods(self):
        """Obtiene la lista completa de todos los alimentos"""
        handler = FoodHandler()
        summary = handler.summarize_dataset(self)
        return summary["foods"]

    def get_food_names(self):
        """Obtiene una lista con los nombres de todos los alimentos"""
        handler = FoodHandler()
        summary = handler.summarize_dataset(self)
        return [food["name"] for food in summary["foods"]]


class FoodDatasetVersion(DatasetVersion):
    """Versión extendida para datasets FOOD con métricas específicas"""

    __tablename__ = "food_dataset_version"

    id = db.Column(db.Integer, db.ForeignKey("dataset_version.id"), primary_key=True)

    # Métricas agregadas
    total_ingredients = db.Column(db.Integer)
    total_recipes = db.Column(db.Integer)

    __mapper_args__ = {"polymorphic_identity": "food"}

    def compare_with(self, other_version):
        """Comparación extendida entre versiones de FOOD"""
        base_comparison = super().compare_with(other_version)

        if not isinstance(other_version, FoodDatasetVersion):
            return base_comparison

        food_changes = {}

        if self.total_ingredients != other_version.total_ingredients:
            food_changes["ingredients"] = {
                "old": other_version.total_ingredients,
                "new": self.total_ingredients,
                "diff": (self.total_ingredients or 0) - (other_version.total_ingredients or 0),
            }

        if self.total_recipes != other_version.total_recipes:
            food_changes["recipes"] = {
                "old": other_version.total_recipes,
                "new": self.total_recipes,
                "diff": (self.total_recipes or 0) - (other_version.total_recipes or 0),
            }

        base_comparison["food_metrics"] = food_changes
        return base_comparison

    def to_dict(self):
        data = super().to_dict()
        data.update({"total_ingredients": self.total_ingredients or 0, "total_recipes": self.total_recipes or 0})
        return data


# ---------------------------
# Métricas/Registros/DOI mapping
# ---------------------------
class DSDownloadRecord(db.Model):
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


class DSViewRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"))
    view_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    view_cookie = db.Column(db.String(36), nullable=False)  # UUID4

    def __repr__(self):
        return f"<View id={self.id} dataset_id={self.dataset_id} date={self.view_date} cookie={self.view_cookie}>"


class DOIMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_doi_old = db.Column(db.String(120))
    dataset_doi_new = db.Column(db.String(120))


# ---------------------------
# Registro de tipos (útil para factorías en servicios/rutas)
# ---------------------------
DATASET_KIND_TO_CLASS = {
    "base": BaseDataset,
    # "uvl": UVLDataset,
    # "gpx": GPXDataset,
    "food": FoodDataset,
}


# Alias retrocompatible
class DataSet(BaseDataset):
    __mapper_args__ = {
        "polymorphic_identity": "base",  # mismo que BaseDataset
        "concrete": False,  # no crea nueva tabla
    }

    # Nota: no se redefine __tablename__, así que sigue apuntando a "data_set"
    pass
