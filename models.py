from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # plan: "free" / "paid"
    plan = db.Column(db.String(20), nullable=False, default="free")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
