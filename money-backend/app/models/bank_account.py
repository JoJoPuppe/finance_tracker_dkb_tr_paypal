from .db import db

class BankAccount(db.Model):
    """Model representing a bank account owned by a user."""
    __tablename__ = 'bank_account'

    id = db.Column(db.Integer, primary_key=True)
    iban = db.Column(db.String(34), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    user = db.relationship("User", back_populates="bank_accounts")
    transactions = db.relationship("BankTransaction", back_populates="bank_account", lazy=True)

    def __repr__(self):
        return f"<BankAccount {self.name} ({self.iban})>"