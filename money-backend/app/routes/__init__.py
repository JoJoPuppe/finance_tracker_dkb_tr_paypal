"""Route modules for the application."""

from .transactions import bp as transactions_bp
from .categories import bp as categories_bp
from .rules import bp as rules_bp
from .users import bp as users_bp
from .bank_accounts import bp as bank_accounts_bp

__all__ = ['transactions_bp', 'categories_bp', 'rules_bp', 'users_bp', 'bank_accounts_bp']