from app import db


class ShoppingCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    data_sets = db.relationship('DataSet', backref='shoppingcart', lazy=True)
    user = db.relationship('User', backref='shoppingcart', lazy=True)

    def __repr__(self):
        return f'Shoppingcart<{self.id}>'
