from datetime import datetime
from .db import db

class Category(db.Model):
    """Model representing a category for bank transactions."""
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    # Add user_id column
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    
    # Existing relationships
    parent = db.relationship("Category", remote_side=[id], backref="subcategories")
    rules = db.relationship("Rule", backref="category", lazy=True)
    transactions = db.relationship("BankTransaction", backref="category", lazy=True)
    # New relationship to User
    user = db.relationship("User", back_populates="categories")
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)