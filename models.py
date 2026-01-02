from flask_login import UserMixin
from extensions import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    plan = db.Column(db.String(50), default='Free')
    
    # Trading Config
    bybit_api_key = db.Column(db.String(255), nullable=True)
    bybit_api_secret = db.Column(db.String(255), nullable=True)
    paper_balance_usdt = db.Column(db.Float, default=1000.0)
    paper_balance_usdc = db.Column(db.Float, default=1000.0)

class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    exchanges = db.Column(db.String(255))
    profitable_count = db.Column(db.Integer)
    # Could store JSON result blob if needed, but keeping it simple
