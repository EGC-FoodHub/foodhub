from datetime import datetime

from app import db


class Hubfile(db.Model):
    __tablename__ = "file"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    checksum = db.Column(db.String(120), nullable=False)
    size = db.Column(db.Integer, nullable=False)

    food_model_id = db.Column(db.Integer, db.ForeignKey("food_model.id"), nullable=True)

    food_model = db.relationship("FoodModel", back_populates="files")

    def __repr__(self):
        return f"<Hubfile {self.name}>"


class HubfileDownloadRecord(db.Model):
    __tablename__ = "file_download_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file.id"))
    download_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    download_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return f"<HubfileDownloadRecord id={self.id} " f"file_id={self.file_id} date={self.download_date}>"


class HubfileViewRecord(db.Model):
    __tablename__ = "file_view_record"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file.id"))
    view_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    view_cookie = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return f"<HubfileViewRecord id={self.id} " f"file_id={self.file_id} date={self.view_date}>"
