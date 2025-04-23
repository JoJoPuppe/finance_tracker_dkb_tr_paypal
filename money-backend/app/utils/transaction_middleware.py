"""
Transaction Middleware System

This module provides a middleware system for processing bank transactions.
Middlewares can be applied both during transaction import and to existing
transactions in the database.
"""
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional, Callable, TypeVar, Generic
from app.models.transaction import BankTransaction

# Type for processed transaction data before it becomes a BankTransaction
TransactionData = Dict[str, Any]
T = TypeVar('T', BankTransaction, TransactionData)

class TransactionMiddleware(Generic[T], ABC):
    """
    Abstract base class for transaction middleware components.
    Each middleware can process either a BankTransaction object (for existing transactions)
    or a dictionary of transaction data (during import).
    """
    
    @abstractmethod
    def process(self, transaction: T) -> T:
        """
        Process a transaction and return the modified transaction.
        
        Args:
            transaction: Either a BankTransaction instance or a dictionary of transaction data
            
        Returns:
            The processed transaction
        """
        pass
    
    def __str__(self) -> str:
        return self.__class__.__name__


class TransactionMiddlewarePipeline:
    """
    A pipeline for processing transactions through a sequence of middlewares.
    Can be used both for existing transactions and during the import process.
    """
    
    def __init__(self, middlewares: Optional[List[TransactionMiddleware]] = None):
        self.middlewares = middlewares or []
        
    def add_middleware(self, middleware: TransactionMiddleware) -> None:
        """Add a middleware to the pipeline."""
        self.middlewares.append(middleware)
        
    def remove_middleware(self, middleware_type: str) -> None:
        """Remove a middleware from the pipeline by its class name."""
        self.middlewares = [m for m in self.middlewares if m.__class__.__name__ != middleware_type]
    
    def process_transaction(self, transaction: T) -> T:
        """
        Process a transaction through all middlewares in the pipeline.
        
        Args:
            transaction: Either a BankTransaction instance or a dictionary of transaction data
            
        Returns:
            The processed transaction after passing through all middlewares
        """
        result = transaction
        for middleware in self.middlewares:
            result = middleware.process(result)
        return result
    
    def process_bulk(self, transactions: List[T]) -> List[T]:
        """
        Process multiple transactions through the middleware pipeline.
        
        Args:
            transactions: A list of transactions (BankTransaction instances or dictionaries)
            
        Returns:
            The processed transactions
        """
        return [self.process_transaction(transaction) for transaction in transactions]
    
    def process_db_transactions(self, filter_func: Optional[Callable[[BankTransaction], bool]] = None) -> None:
        """
        Process existing transactions in the database through the middleware pipeline.
        
        Args:
            filter_func: Optional function to filter which transactions to process
        """
        from app.models.db import db
        
        # Query all transactions, applying filter if provided
        query = BankTransaction.query
        if filter_func:
            # We can't directly filter with a Python function, so we'll filter after fetching
            transactions = [tx for tx in query.all() if filter_func(tx)]
        else:
            transactions = query.all()
        
        # Process each transaction
        for transaction in transactions:
            processed = self.process_transaction(transaction)
            # The process_transaction function returns the same object, already modified
            # So we don't need to do anything else here
        
        # Commit the changes to the database
        db.session.commit()

# Global pipeline instance that can be configured at application startup
transaction_pipeline = TransactionMiddlewarePipeline()