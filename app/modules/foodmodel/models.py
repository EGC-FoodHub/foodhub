from app import db


class FoodModel(db.Model):
    __tablename__ = "food_model"

    id = db.Column(db.Integer, primary_key=True)

    data_set_id = db.Column(db.Integer, db.ForeignKey("food_dataset.id"), nullable=False)

    dataset = db.relationship("FoodDataset", back_populates="files")

    food_meta_data_id = db.Column(db.Integer, db.ForeignKey("food_meta_data.id"))
    food_meta_data = db.relationship("FoodMetaData", back_populates="food_model", cascade="all, delete")

    files = db.relationship("Hubfile", back_populates="food_model", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FoodModel {self.id}>"

    @property
    def size_in_bytes(self):
        return sum(file.size for file in self.files)


class FoodMetaData(db.Model):
    __tablename__ = "food_meta_data"

    id = db.Column(db.Integer, primary_key=True)
    food_filename = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(db.String(50))
    publication_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))

    food_model = db.relationship("FoodModel", back_populates="food_meta_data", uselist=False)

    authors = db.relationship(
        "app.modules.basedataset.models.BaseAuthor",
        backref="food_metadata",
        lazy=True,
        cascade="all, delete",
        foreign_keys="app.modules.basedataset.models.BaseAuthor.food_meta_data_id",
    )

    def __repr__(self):
        return f"<FoodMetaData {self.title}>"
