"""
Utility script to generate transaction hashes for existing transactions.
This should be run after adding the transaction_hash column to the database.

Run with:
python -m app.utils.generate_transaction_hashes
"""

import hashlib
import logging
from ..models.db import db
from ..models.transaction import BankTransaction
from flask import current_app

# Set up logger
logger = logging.getLogger("money_backend.transaction_hashes")


def generate_transaction_hash(tx):
    """
    Generate a unique hash for a transaction to identify duplicates.
    This is the same function as in the routes/transactions/__init__.py file.
    """
    # Convert dates to strings if they're not None, otherwise use empty string
    booking_date_str = tx.booking_date.isoformat() if tx.booking_date else ""
    value_date_str = tx.value_date.isoformat() if tx.value_date else ""

    # Create a string combining all the values
    transaction_str = (
        f"{booking_date_str}|{value_date_str}|{str(tx.amount)}|"
        f"{tx.payee or ''}|{tx.payer or ''}|{tx.purpose or ''}|"
        f"{tx.transaction_type or ''}|{tx.iban or ''}"
    )

    # Generate an MD5 hash of the combined string
    return hashlib.md5(transaction_str.encode("utf-8")).hexdigest()


def setup_logging():
    """Set up logging if run as standalone script"""
    if not logger.handlers:
        # Logger setup will be handled by the main app logger if used as a module
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


def update_transaction_hashes():
    """
    Update the transaction_hash field for all transactions that don't have one.
    """
    logger.info("Starting transaction hash generation...")

    # Get all transactions without a hash
    transactions = BankTransaction.query.filter(
        BankTransaction.transaction_hash.is_(None)
    ).all()
    total = len(transactions)

    logger.info(f"Found {total} transactions without hashes")

    # Track duplicate hashes to report potential issues
    hash_counter = {}
    updated = 0
    duplicates = 0

    for i, tx in enumerate(transactions):
        tx_hash = generate_transaction_hash(tx)

        # Check if this hash already exists in the database
        existing = BankTransaction.query.filter_by(transaction_hash=tx_hash).first()

        if existing and existing.id != tx.id:
            # Duplicate transaction found
            duplicates += 1
            logger.warning(
                f"Duplicate found: Transaction ID {tx.id} and {existing.id} have the same hash {tx_hash}"
            )
            logger.warning(f"  - Tx1: {tx.booking_date} | {tx.payee} | {tx.amount}")
            logger.warning(
                f"  - Tx2: {existing.booking_date} | {existing.payee} | {existing.amount}"
            )
        else:
            # No duplicate, safe to assign the hash
            tx.transaction_hash = tx_hash
            updated += 1

        # Track hash frequency
        hash_counter[tx_hash] = hash_counter.get(tx_hash, 0) + 1

        # Log progress every 100 transactions
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{total} transactions")

    # Commit all changes
    db.session.commit()

    # Report results
    logger.info("\nHash generation complete!")
    logger.info(f"Updated {updated} transactions with hashes")
    logger.info(f"Found {duplicates} potential duplicate transactions")

    # Report any hashes with more than one occurrence
    duplicate_hashes = {h: count for h, count in hash_counter.items() if count > 1}
    if duplicate_hashes:
        logger.warning(f"Found {len(duplicate_hashes)} hash collisions:")
        for tx_hash, count in duplicate_hashes.items():
            logger.warning(f"Hash {tx_hash} appears {count} times")

    return updated, duplicates


if __name__ == "__main__":
    # Import and create app to get the application context
    from app import create_app

    setup_logging()
    app = create_app()

    with app.app_context():
        update_transaction_hashes()

