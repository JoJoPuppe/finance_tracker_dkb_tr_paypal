from datetime import datetime
from .db import db

class Rule(db.Model):
    """Model representing a categorization rule."""
    __tablename__ = 'rule'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    
    logical_operator = db.Column(db.String(10), nullable=False, default="AND")  # AND or OR
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    conditions = db.relationship("RuleCondition", backref="rule", lazy=True, cascade="all, delete-orphan")
    user = db.relationship("User", back_populates="rules")
    
    def __repr__(self):
        return f"<Rule(id={self.id}, name='{self.name}', category_id={self.category_id})>"


class RuleCondition(db.Model):
    """Model representing a single condition within a rule."""
    __tablename__ = 'rule_condition'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('rule.id'), nullable=False)
    field = db.Column(db.String(255), nullable=False)
    operator = db.Column(db.String(50), nullable=False)  # equals, contains, greater_than, etc.
    value = db.Column(db.String(255), nullable=False)
    sequence = db.Column(db.Integer, default=0)  # For maintaining condition order
    
    def __repr__(self):
        return f"<Condition(id={self.id}, field='{self.field}', operator='{self.operator}', value='{self.value})'>"