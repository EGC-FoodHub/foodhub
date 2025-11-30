import re

import unidecode
from sqlalchemy import any_, or_

# Usamos los modelos Base y Food si es necesario
from app.modules.basedataset.models import BaseAuthor, BaseDataset, BaseDSMetaData, BasePublicationType
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDataset)

    def filter(self, query="", sorting="newest", publication_type="any", tags=[], **kwargs):
        # Normalize and remove unwanted characters
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

        filters = []
        for word in cleaned_query.split():
            # Filtros Genéricos (BaseDSMetaData)
            filters.append(BaseDSMetaData.title.ilike(f"%{word}%"))
            filters.append(BaseDSMetaData.description.ilike(f"%{word}%"))
            filters.append(BaseDSMetaData.tags.ilike(f"%{word}%"))

            # Filtros de Autor
            filters.append(BaseAuthor.name.ilike(f"%{word}%"))
            filters.append(BaseAuthor.affiliation.ilike(f"%{word}%"))
            filters.append(BaseAuthor.orcid.ilike(f"%{word}%"))

            # Filtros de Fecha
            filters.append(BaseDataset.created_at.ilike(f"%{word}%"))

            # --- ELIMINADOS: Filtros de UVL/FeatureModel ---

        datasets = (
            self.model.query.join(BaseDSMetaData)  # Join genérico
            .join(BaseDSMetaData.authors)  # Join con autores
            # --- ELIMINADOS: Joins con feature_models y fm_meta_data ---
            .filter(or_(*filters))
            .filter(BaseDSMetaData.dataset_doi.isnot(None))  # Exclude datasets without DOI
        )

        if publication_type != "any":
            matching_type = None
            for member in BasePublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break

            if matching_type is not None:
                datasets = datasets.filter(BaseDSMetaData.publication_type == matching_type.name)

        if tags:
            datasets = datasets.filter(BaseDSMetaData.tags.ilike(any_(f"%{tag}%" for tag in tags)))

        # Order by created_at
        if sorting == "oldest":
            datasets = datasets.order_by(self.model.created_at.asc())
        else:
            datasets = datasets.order_by(self.model.created_at.desc())

        return datasets.all()
