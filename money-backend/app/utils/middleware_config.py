"""
Middleware configuration module.

This module sets up the global transaction middleware pipeline.
"""

from app.models import transaction
from app.utils.transaction_middleware import transaction_pipeline
from app.utils.transaction_middlewares import (
    DataCleaningMiddleware,
    ApplyRulesMiddleware,
    InternalTransferDetectionMiddleware,
    TransactionHashMiddleware,
    DateFormattingMiddleware,
)


def configure_transaction_middlewares():
    """
    Configure the global transaction middleware pipeline with default middleware components.
    This function should be called during application initialization.
    """
    # Clear any existing middleware first
    transaction_pipeline.middlewares = []

    # Add middleware in the desired processing order

    # 1. First, clean and normalize the data
    transaction_pipeline.add_middleware(DataCleaningMiddleware())

    # 2. Generate transaction hash for duplicate detection
    transaction_pipeline.add_middleware(TransactionHashMiddleware())

    # 3. Detect internal transfers between own accounts
    transaction_pipeline.add_middleware(InternalTransferDetectionMiddleware())

    # 4. Apply categorization rules
    transaction_pipeline.add_middleware(ApplyRulesMiddleware())

    transaction_pipeline.add_middleware(DateFormattingMiddleware())

    # Additional middlewares can be added here based on configuration or other requirements

    return transaction_pipeline

