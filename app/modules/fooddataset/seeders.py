import os
import shutil
from datetime import datetime, timezone

from app.modules.auth.models import User
from app.modules.basedataset.models import BaseAuthor, BasePublicationType
from app.modules.fooddataset.models import FoodDataset, FoodDSMetaData, FoodNutritionalValue
from app.modules.foodmodel.models import FoodMetaData, FoodModel
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class FooddatasetSeeder(BaseSeeder):

    priority = 2  # Lower priority

    def run(self):
        # Retrieve users
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()

        if not user1 or not user2:
            raise Exception("Users not found. Please seed users first.")

        # Source folder for food examples
        working_dir = os.getcwd()
        src_folder = os.path.join(working_dir, "app", "modules", "fooddataset", "food_examples")

        if not os.path.exists(src_folder):
            print(f"Source folder not found: {src_folder}")
            return

        # List all .food files
        food_files = [f for f in os.listdir(src_folder) if f.endswith(".food")]

        datasets_to_create = 4
        seeded_datasets = []
        seeded_ds_meta_data = []

        # 1. Create Datasets and Metadata (Dataset Level)
        for i in range(datasets_to_create):
            user = user1 if i % 2 == 0 else user2

            # Author from user profile
            author_name = user.profile.name if user.profile and user.profile.name else "Unknown"
            author_surname = user.profile.surname if user.profile and user.profile.surname else "Author"
            full_author_name = f"{author_surname}, {author_name}"

            ds_meta_data = FoodDSMetaData(
                title=f"Food Dataset {i+1}",
                description=f"A collection of food models #{i+1}",
                publication_type=BasePublicationType.DATA_MANAGEMENT_PLAN,  # Default from legacy
                publication_doi=f"10.1234/food-dataset-{i+1}",
                dataset_doi=f"10.1234/food-dataset-{i+1}",
                tags="food, dataset",
                calories="2000",  # Dummy value
                type="Menu",  # Dummy value
            )
            # Seed metadata first to get ID
            ds_meta_data = self.seed([ds_meta_data])[0]
            seeded_ds_meta_data.append(ds_meta_data)

            # Create Author for Dataset
            author = BaseAuthor(
                name=full_author_name,
                affiliation=user.profile.affiliation if user.profile else "FoodHub",
                orcid=user.profile.orcid if user.profile else "0000-0000-0000-0000",
                food_ds_meta_data_id=ds_meta_data.id,
            )
            self.seed([author])

            # Create Dataset
            dataset = FoodDataset(
                user_id=user.id, ds_meta_data_id=ds_meta_data.id, created_at=datetime.now(timezone.utc)
            )
            dataset = self.seed([dataset])[0]
            seeded_datasets.append(dataset)

        # 2. Assign Food Models (.food files) to Datasets
        # We distribute the found files among the created datasets

        for idx, file_name in enumerate(food_files):
            # Round robin assignment
            dataset_idx = idx % datasets_to_create
            dataset = seeded_datasets[dataset_idx]
            user_id = dataset.user_id

            # Name without extension
            base_name = os.path.splitext(file_name)[0]
            title = base_name.replace("_", " ").title()

            # Create FoodMetaData (Model Level)
            food_meta_data = FoodMetaData(
                food_filename=file_name,
                title=title,
                description=f"Nutritional info for {title}",
                publication_type="Food Description",
                tags="food, healthy",
            )
            food_meta_data = self.seed([food_meta_data])[0]

            # Create Author for Food Model

            user = user1 if dataset.user_id == user1.id else user2
            author_name = user.profile.name if user.profile and user.profile.name else "Unknown"
            author_surname = user.profile.surname if user.profile and user.profile.surname else "Author"
            full_author_name = f"{author_surname}, {author_name}"

            model_author = BaseAuthor(
                name=full_author_name,
                affiliation=user.profile.affiliation if user.profile else "FoodHub",
                food_meta_data_id=food_meta_data.id,
            )
            self.seed([model_author])

            # Create FoodModel
            food_model = FoodModel(data_set_id=dataset.id, food_meta_data_id=food_meta_data.id)
            food_model = self.seed([food_model])[0]

            # Copy file
            dest_folder = os.path.join(working_dir, "uploads", f"user_{user_id}", f"dataset_{dataset.id}")
            os.makedirs(dest_folder, exist_ok=True)

            src_file_path = os.path.join(src_folder, file_name)
            dest_file_path = os.path.join(dest_folder, file_name)

            shutil.copy(src_file_path, dest_folder)
            file_size = os.path.getsize(dest_file_path)

            # Create Hubfile
            hubfile = Hubfile(
                name=file_name,
                checksum=f"checksum-{idx}",  # Dummy checksum
                size=file_size,
                food_model_id=food_model.id,
            )
            self.seed([hubfile])

            # Parse the .food file to get calories
            calories_value = "0 kcal"  # Default
            try:
                with open(src_file_path, "r") as f:
                    for line in f:
                        if line.strip().startswith("calories:"):
                            calories_value = line.split(":", 1)[1].strip()
                            break
            except Exception as e:
                print(f"Error parsing {file_name}: {e}")

            # Add nutritional value to the DATASET metadata
            nutval = FoodNutritionalValue(
                ds_meta_data_id=dataset.ds_meta_data_id, name=f"Energy ({title})", value=calories_value
            )
            self.seed([nutval])

        # Index seeded datasets in Elasticsearch
        try:
            from core.services.SearchService import SearchService

            search_service = SearchService()
            if search_service.enabled:
                print("Indexing seeded datasets in Elasticsearch...")
                for dataset in seeded_datasets:
                    search_service.index_dataset(dataset)
        except Exception as e:
            print(f"Error indexing seeded datasets: {e}")
