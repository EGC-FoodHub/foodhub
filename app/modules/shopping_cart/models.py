from app import db


class ShoppingCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    data_sets = db.relationship('DataSet', backref='shoppingCart', lazy=True)
    user = db.relationship('User', backref='shoppingCart', lazy=True)

    def __repr__(self):
        return f'Shoppingcart<{self.id}>'

    def get_total_amount_from_file_sizes_for_human(self):
        from app.modules.dataset.services import SizeService

        sum = 0
        for data_set in self.data_sets:
            sum += data_set.get_file_total_size()

        return SizeService().get_human_readable_size(sum)


