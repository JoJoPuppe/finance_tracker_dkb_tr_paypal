from .db import db

class User(db.Model):
    """Model representing a user of the application."""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    categories = db.relationship('Category', back_populates='user', lazy=True)
    rules = db.relationship('Rule', back_populates='user', lazy=True)
    bank_accounts = db.relationship('BankAccount', back_populates='user', lazy=True)

    def __repr__(self):
        return f"<User {self.name}>"