"""
Transaction Middleware Implementations

This module provides concrete implementations of transaction middleware components
that can be added to the middleware pipeline.
"""

from datetime import datetime
from typing import Dict, Any, Union, Optional, List, Pattern
import re
from decimal import Decimal
import hashlib

from app.models.transaction import BankTransaction
from app.utils.transaction_middleware import TransactionMiddleware, TransactionData
from app.models.rule import Rule
from app.utils.rule_engine import RuleEngine
from app.config import config

T = Union[BankTransaction, TransactionData]


class DateFormattingMiddleware(TransactionMiddleware[T]):
    """
    Middleware for cleaning and normalizing transaction data.
    Handles operations like trimming whitespace, standardizing formats, etc.
    """

    def parse_date(self, date_str, format="%d.%m.%y"):
        INPUT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
        if "T" in date_str:
            try:
                return datetime.strptime(date_str, INPUT_DATE_FORMAT)
            except (ValueError, TypeError):
                return None
        else:
            try:
                return datetime.strptime(date_str, format).date()
            except Exception:
                return None

    def process(self, transaction: T) -> T:
        if isinstance(transaction, dict):
            if "booking_date" in transaction and transaction["booking_date"]:
                transaction["booking_date"] = self.parse_date(
                    transaction["booking_date"]
                )
            if "value_date" in transaction and transaction["value_date"]:
                transaction["value_date"] = self.parse_date(transaction["value_date"])
        else:
            if transaction.booking_date:
                transaction.booking_date = self.parse_date(
                    transaction.booking_date.strip()
                )
            if transaction.value_date:
                transaction.value_date = self.parse_date(transaction.value_date.strip())

        return transaction


class DataCleaningMiddleware(TransactionMiddleware[T]):
    """
    Middleware for cleaning and normalizing transaction data.
    Handles operations like trimming whitespace, standardizing formats, etc.
    """

    def process(self, transaction: T) -> T:
        if isinstance(transaction, dict):
            # Clean transaction data dictionary during import
            if "purpose" in transaction and transaction["purpose"]:
                transaction["purpose"] = transaction["purpose"].strip()
            if "payee" in transaction and transaction["payee"]:
                transaction["payee"] = transaction["payee"].strip()
            if "payer" in transaction and transaction["payer"]:
                transaction["payer"] = transaction["payer"].strip()

            # Convert amount strings to proper floats if needed
            if "amount" in transaction and isinstance(transaction["amount"], str):
                # Remove any thousands separators and convert decimal comma to point
                amount_str = transaction["amount"].replace(".", "").replace(",", ".")
                try:
                    transaction["amount"] = float(amount_str)
                except ValueError:
                    pass  # Keep the original value if conversion fails
            if transaction["iban"] == config.TRADEREPUBLIC_SAVING_PLAN_IBAN:
                transaction["iban"] = config.TRADEREPUBLIC_IBAN
        else:
            # Clean BankTransaction object fields
            if transaction.purpose:
                transaction.purpose = transaction.purpose.strip()
            if transaction.payee:
                transaction.payee = transaction.payee.strip()
            if transaction.payer:
                transaction.payer = transaction.payer.strip()
            # replace Traderepublic saving plan IBAN with own TR IBAN
            if transaction.iban == config.TRADEREPUBLIC_SAVING_PLAN_IBAN:
                transaction.iban = config.TRADEREPUBLIC_IBAN

        return transaction


class ApplyRulesMiddleware(TransactionMiddleware[T]):
    """
    Middleware for applying categorization rules to transactions.
    """

    def __init__(self, rules: Optional[List[Rule]] = None):
        """
        Initialize with rules or load them from the database.

        Args:
            rules: Optional list of Rule objects. If None, rules will be loaded from the database.
        """
        self.rules = rules
        self._rules_loaded = False

    def _load_rules(self):
        """Load rules from the database if they haven't been provided."""
        if not self._rules_loaded:
            from app.models.rule import Rule
            from sqlalchemy.orm import joinedload
            from app.models.db import db
            
            # Use joinedload to eagerly load rule conditions to prevent detached instance errors
            self.rules = Rule.query.options(joinedload(Rule.conditions)).order_by(Rule.created_at).all()
            
            # Ensure all rule conditions are accessed within this session context
            for rule in self.rules:
                # Touch the conditions to ensure they're loaded
                _ = list(rule.conditions)
            
            self._rules_loaded = True

    def process(self, transaction: T) -> T:
        """Process a transaction by applying rules to it."""
        try:
            # Make sure we have rules loaded and they're attached to a session
            self._load_rules()
            
            if isinstance(transaction, dict):
                # For transaction data dictionary, we can't directly apply rules
                # We'd need to create a temporary BankTransaction object
                temp_transaction = BankTransaction()
                for key, value in transaction.items():
                    if hasattr(temp_transaction, key):
                        setattr(temp_transaction, key, value)

                # Apply rules
                matched, category_id, rule_id = RuleEngine.apply_rules(
                    temp_transaction, self.rules
                )
                if matched:
                    transaction["category_id"] = category_id
                    transaction["rule_id"] = rule_id
            else:
                # For BankTransaction object, apply rules directly
                if not transaction.category_id:  # Only apply if not already categorized
                    matched, category_id, rule_id = RuleEngine.apply_rules(
                        transaction, self.rules
                    )
                    if matched:
                        transaction.category_id = category_id
                        transaction.rule_id = rule_id

            return transaction
        except Exception as e:
            # Log the error but continue processing
            import logging
            logger = logging.getLogger('money_backend.transaction_middlewares')
            logger.error(f"Error in ApplyRulesMiddleware: {str(e)}")
            return transaction


class InternalTransferDetectionMiddleware(TransactionMiddleware[T]):
    """
    Middleware for detecting internal transfers between own bank accounts.
    """

    def __init__(self, own_ibans: Optional[List[str]] = None):
        """
        Initialize with own IBANs or load them from the database.

        Args:
            own_ibans: Optional list of own IBANs. If None, IBANs will be loaded from the database.
        """
        self.own_ibans = own_ibans

    def _load_ibans(self):
        """Load own IBANs from the database if they haven't been provided."""
        if self.own_ibans is None:
            from app.models.bank_account import BankAccount

            accounts = BankAccount.query.all()
            self.own_ibans = [account.iban for account in accounts if account.iban]

    def process(self, transaction: T) -> T:
        self._load_ibans()

        if isinstance(transaction, dict):
            # For transaction data dictionary
            is_internal = False

            # Check if both the transaction IBAN and counterparty IBAN are in our own IBANs
            iban = transaction.get("iban")
            counterparty_iban = transaction.get("counterparty_iban")

            if iban and counterparty_iban:
                is_internal = (
                    iban in self.own_ibans and counterparty_iban in self.own_ibans
                )

            transaction["is_internal_transfer"] = is_internal
        else:
            # For BankTransaction object
            is_internal = False

            if transaction.iban and transaction.counterparty_iban:
                is_internal = (
                    transaction.iban in self.own_ibans
                    and transaction.counterparty_iban in self.own_ibans
                )

            transaction.is_internal_transfer = is_internal

        return transaction


class TransactionHashMiddleware(TransactionMiddleware[T]):
    """
    Middleware for generating a unique hash for each transaction to identify duplicates.
    """

    def process(self, transaction: T) -> T:
        if isinstance(transaction, dict):
            # For transaction data dictionary, create hash based on key fields
            hash_input = (
                f"{transaction.get('booking_date', '')}"
                f"{transaction.get('value_date', '')}"
                f"{transaction.get('amount', '')}"
                f"{transaction.get('payee', '')}"
                f"{transaction.get('purpose', '')}"
            )
            transaction["transaction_hash"] = hashlib.md5(
                hash_input.encode("utf-8")
            ).hexdigest()
        else:
            # For BankTransaction object, create hash if not already present
            if not transaction.transaction_hash:
                hash_input = (
                    f"{transaction.booking_date}"
                    f"{transaction.value_date}"
                    f"{transaction.amount}"
                    f"{transaction.payee}"
                    f"{transaction.purpose}"
                )
                transaction.transaction_hash = hashlib.md5(
                    hash_input.encode("utf-8")
                ).hexdigest()

        return transaction


class PatternExtractionMiddleware(TransactionMiddleware[T]):
    """
    Middleware for extracting specific patterns from transaction descriptions.
    Useful for getting reference numbers, invoice IDs, etc.
    """

    def __init__(self, patterns: Dict[str, Pattern]):
        """
        Initialize with regex patterns to extract.

        Args:
            patterns: Dictionary mapping field names to regex patterns
        """
        self.patterns = patterns

    def process(self, transaction: T) -> T:
        # We'll extract from purpose field
        if isinstance(transaction, dict):
            purpose = transaction.get("purpose", "")
            if purpose:
                for field_name, pattern in self.patterns.items():
                    match = pattern.search(purpose)
                    if match:
                        transaction[field_name] = match.group(1)
        else:
            if transaction.purpose:
                for field_name, pattern in self.patterns.items():
                    match = pattern.search(transaction.purpose)
                    if match and hasattr(transaction, field_name):
                        setattr(transaction, field_name, match.group(1))

        return transaction


class EnrichmentMiddleware(TransactionMiddleware[T]):
    """
    Middleware for enriching transaction data with additional information.
    This can include fetching merchant details, categorization based on ML models, etc.
    """

    def __init__(self, enrichment_function):
        """
        Initialize with a function that enriches transaction data.

        Args:
            enrichment_function: A function that takes a transaction and returns an enriched version
        """
        self.enrichment_function = enrichment_function

    def process(self, transaction: T) -> T:
        # Pass the transaction through the enrichment function
        return self.enrichment_function(transaction)
