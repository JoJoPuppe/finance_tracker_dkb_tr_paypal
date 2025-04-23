from .db import db

class BankTransaction(db.Model):
    """Model representing a bank transaction."""
    __tablename__ = 'bank_transaction'

    id = db.Column(db.Integer, primary_key=True)
    booking_date = db.Column(db.Date)
    value_date = db.Column(db.Date)
    status = db.Column(db.String(50))
    payer = db.Column(db.String(255))
    payee = db.Column(db.String(255))
    purpose = db.Column(db.Text)
    transaction_type = db.Column(db.String(50))
    iban = db.Column(db.String(34))
    amount = db.Column(db.Float)
    creditor_id = db.Column(db.String(255))
    mandate_reference = db.Column(db.String(255))
    customer_reference = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    transaction_hash = db.Column(db.String(32), unique=True, index=True, nullable=True)
    rule_id = db.Column(db.Integer, db.ForeignKey("rule.id"), nullable=True)
    
    # New fields for bank account management
    bank_account_id = db.Column(db.Integer, db.ForeignKey("bank_account.id"), nullable=True)
    counterparty_iban = db.Column(db.String(34), nullable=True, index=True)
    is_internal_transfer = db.Column(db.Boolean, default=False)
    
    # The category relationship is already defined in the Category model with backref
    # So we don't need to define it here again
    # Define relationship to Rule model
    applied_rule = db.relationship("Rule", foreign_keys=[rule_id], backref=db.backref("transactions", lazy=True))
    
    # New relationship to BankAccount
    bank_account = db.relationship("BankAccount", back_populates="transactions")
    
    def __repr__(self):
        return f"<BankTransaction {self.id}: {self.amount}>"