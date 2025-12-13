import re

import unidecode
from sqlalchemy import any_, or_

from app.modules.basedataset.models import BaseAuthor, BaseDataset, BaseDSMetaData, BasePublicationType
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseDataset)

    def filter(self, query="", sorting="newest", publication_type="any", tags=[], **kwargs):
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

        filters = []
        for word in cleaned_query.split():
            filters.append(BaseDSMetaData.title.ilike(f"%{word}%"))
            filters.append(BaseDSMetaData.description.ilike(f"%{word}%"))
            filters.append(BaseDSMetaData.tags.ilike(f"%{word}%"))

            filters.append(BaseAuthor.name.ilike(f"%{word}%"))
            filters.append(BaseAuthor.affiliation.ilike(f"%{word}%"))
            filters.append(BaseAuthor.orcid.ilike(f"%{word}%"))

            filters.append(BaseDataset.created_at.ilike(f"%{word}%"))

        datasets = (
            self.model.query.join(BaseDSMetaData)
            .join(BaseDSMetaData.authors)
            .filter(or_(*filters))
            .filter(BaseDSMetaData.dataset_doi.isnot(None))
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

        if sorting == "oldest":
            datasets = datasets.order_by(self.model.created_at.asc())
        else:
            datasets = datasets.order_by(self.model.created_at.desc())

        return datasets.all()

    def get_by_ids(self, ids):
        if not ids:
            return []

        query = self.model.query.filter(self.model.id.in_(ids))

        datasets = query.all()

        datasets_map = {d.id: d for d in datasets}
        ordered_datasets = [datasets_map[id] for id in ids if id in datasets_map]

        return ordered_datasets
