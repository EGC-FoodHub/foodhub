from app import db


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)

    orcid = db.Column(db.String(19))
    affiliation = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    uploaded_datasets_count = db.Column(db.Integer, default=0)
    downloaded_datasets_count = db.Column(db.Integer, default=0)
    synchronized_datasets_count = db.Column(db.Integer, default=0)

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()
