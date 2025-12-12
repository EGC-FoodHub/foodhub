import os

from elasticsearch import Elasticsearch


class SearchService:
    def __init__(self):
        self.enabled = True

        elastic_url = os.getenv("ELASTICSEARCH_URL")
        elastic_password = os.getenv("ELASTICSEARCH_PASSWORD")

        if not elastic_url or not elastic_password:
            print("❌ ERROR: Faltan ELASTICSEARCH_URL o ELASTICSEARCH_PASSWORD en el archivo .env")
            self.enabled = False
            return

        self.es = Elasticsearch(elastic_url, basic_auth=("elastic", elastic_password))

    def index_dataset(self, dataset):
        try:
            metadata = dataset.ds_meta_data

            if metadata is None:
                print(f"⚠️ El dataset {dataset.id} no tiene metadatos vinculados todavía.")
                return

            pub_type = metadata.publication_type
            if hasattr(pub_type, "name"):
                pub_type = pub_type.name

            document = {
                "id": dataset.id,
                "title": metadata.title,
                "description": metadata.description,
                "publication_type": pub_type,
                "tags": metadata.tags,
                "calories": int(metadata.calories) if metadata.calories and metadata.calories.isdigit() else 0,
                "created_at": dataset.created_at.isoformat(),
            }

            self.es.index(index="datasets", id=dataset.id, document=document)
            print(f"✅ Dataset {dataset.id} ('{metadata.title}') indexado correctamente en Elastic.")

        except Exception as e:
            print(f"❌ Error indexing dataset: {e}")

    def search_datasets(self, query, sorting=None, publication_type=None, tags=None, **kwargs):
        try:
            must_clauses = []
            filter_clauses = []

            if not query or query.strip() == "":
                must_clauses.append({"match_all": {}})
            else:
                search_query = f"*{query}*"
                must_clauses.append(
                    {
                        "query_string": {
                            "query": search_query,
                            "fields": ["title", "description", "tags"],
                            "default_operator": "AND",
                        }
                    }
                )

            # Filter by calories
            calories_min = kwargs.get("calories_min")
            calories_max = kwargs.get("calories_max")

            if calories_min or calories_max:
                range_query = {"calories": {}}
                if calories_min:
                    range_query["calories"]["gte"] = int(calories_min)
                if calories_max:
                    range_query["calories"]["lte"] = int(calories_max)
                filter_clauses.append({"range": range_query})

            search_body = {"query": {"bool": {"must": must_clauses, "filter": filter_clauses}}}

            response = self.es.search(index="datasets", body=search_body)

            hits = response["hits"]["hits"]
            ids = [int(hit["_id"]) for hit in hits]

            print(f"🔍 Búsqueda Elastic para '{query}': Encontrados IDs {ids}")
            return ids

        except Exception as e:
            print(f"❌ Error searching in Elastic: {e}")
            return []
