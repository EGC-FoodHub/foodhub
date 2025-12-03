from app import db


class FoodChecker(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f"FoodChecker<{self.id}>"
