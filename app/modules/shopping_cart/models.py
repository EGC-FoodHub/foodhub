import datetime

from app import db


class ShoppingCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    food_data_sets = db.relationship("FoodDataset", backref="shoppingCart", lazy=True)
    user = db.relationship("User", backref="shoppingCart", lazy=True)

    def __repr__(self):
        return f"Shoppingcart<{self.id}>"

    def get_total_amount_from_file_sizes_for_human(self):
        from app.modules.fooddataset.services import SizeService

        sum = 0
        for data_set in self.food_data_sets:
            sum += data_set.get_file_total_size()

        return SizeService().get_human_readable_size(sum)


'''

APARTIR DE AQUI ES DE LA NUEVA IMPLEMENTACIÓN

'''

# Esto es para tener una tabla de "rescate"
download_record_datasets = db.Table('download_record_datasets',
                                    db.Column('download_record_id', db.Integer, db.ForeignKey('download_record.id'),
                                              primary_key=True),
                                    db.Column('food_dataset_id', db.Integer, db.ForeignKey('food_dataset.id'),
                                              primary_key=True)
                                    )


class DownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)

    # Relaciona el resto de tablas que se ven afectadas para que Alembic y Flask no exploten
    user = db.relationship("User", backref="download_history", lazy=True)
    
    # Relación con los datasets
    datasets = db.relationship("FoodDataset", secondary=download_record_datasets, lazy='subquery')

    def __repr__(self):
        return f"DownloadRecord<{self.id} - {self.created_at}>"
