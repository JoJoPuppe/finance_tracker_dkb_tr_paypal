"""
Transaction Service

This module provides services for processing bank transactions using the middleware pipeline.
It serves as the main entry point for all transaction processing operations.
"""
from typing import List, Dict, Any, Optional, Union, Callable
import logging
import traceback
from app.models.db import db
from app.models.transaction import BankTransaction
from app.utils.transaction_middleware import transaction_pipeline, TransactionData

# Set up logger
logger = logging.getLogger('money_backend.transaction_service')

class TransactionService:
    """
    Service for processing bank transactions through the middleware pipeline.
    """
    
    @staticmethod
    def process_import_data(transaction_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of transaction dictionaries during import.
        
        Args:
            transaction_data_list: List of dictionaries containing transaction data
            
        Returns:
            The processed transaction data
        """
        logger.info(f"Processing {len(transaction_data_list)} transactions through middleware pipeline")
        try:
            # Process all transactions through the middleware pipeline
            processed_data = transaction_pipeline.process_bulk(transaction_data_list)
            logger.debug(f"Successfully processed {len(processed_data)} transactions through middleware")
            return processed_data
        except Exception as e:
            logger.error(f"Error processing transactions through middleware: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def save_transactions(transaction_data_list: List[Dict[str, Any]]) -> List[BankTransaction]:
        """
        Save a list of processed transaction data to the database.
        
        Args:
            transaction_data_list: List of dictionaries containing processed transaction data
            
        Returns:
            List of created BankTransaction objects
        """
        logger.info(f"Saving {len(transaction_data_list)} transactions to database")
        saved_transactions = []
        duplicates = 0
        
        try:
            for i, data in enumerate(transaction_data_list):
                try:
                    # Check if a transaction with this hash already exists
                    if 'transaction_hash' in data:
                        existing = BankTransaction.query.filter_by(
                            transaction_hash=data['transaction_hash']
                        ).first()
                        
                        if existing:
                            # Skip this transaction, it's a duplicate
                            duplicates += 1
                            logger.debug(f"Skipping duplicate transaction with hash {data['transaction_hash']}")
                            continue
                    else:
                        logger.warning(f"Transaction at index {i} has no transaction_hash")
                
                    # Create new transaction object
                    transaction = BankTransaction()
                    
                    # Set attributes from data dictionary
                    for key, value in data.items():
                        if hasattr(transaction, key):
                            setattr(transaction, key, value)
                        else:
                            logger.warning(f"Attribute '{key}' in transaction data does not exist on BankTransaction model")
                    
                    db.session.add(transaction)
                    saved_transactions.append(transaction)
                    
                except Exception as e:
                    logger.error(f"Error saving transaction at index {i}: {str(e)}")
                    logger.error(f"Transaction data: {data}")
                    logger.error(f"Stack trace: {traceback.format_exc()}")
                    # Don't raise here, continue with other transactions
            
            # Commit all transactions
            logger.info(f"Committing {len(saved_transactions)} transactions to database")
            db.session.commit()
            logger.info(f"Successfully saved {len(saved_transactions)} transactions, skipped {duplicates} duplicates")
            
            return saved_transactions
            
        except Exception as e:
            logger.error(f"Database error while saving transactions: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            db.session.rollback()
            raise
    
    @staticmethod
    def import_and_save_transactions(transaction_data_list: List[Dict[str, Any]]) -> List[BankTransaction]:
        """
        Process and save a list of transaction data.
        
        Args:
            transaction_data_list: List of dictionaries containing transaction data
            
        Returns:
            List of created BankTransaction objects
        """
        logger.info(f"Starting import and save of {len(transaction_data_list)} transactions")
        
        try:
            # First process the data through middlewares
            processed_data = TransactionService.process_import_data(transaction_data_list)
            
            # Then save to database
            result = TransactionService.save_transactions(processed_data)
            
            logger.info(f"Successfully imported and saved {len(result)} transactions")
            return result
        except Exception as e:
            logger.error(f"Failed to import and save transactions: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            db.session.rollback()
            raise
    
    @staticmethod
    def process_existing_transactions(filter_func: Optional[Callable[[BankTransaction], bool]] = None) -> int:
        """
        Process existing transactions in the database through the middleware pipeline.
        
        Args:
            filter_func: Optional function to filter which transactions to process
            
        Returns:
            Number of transactions processed
        """
        logger.info("Processing existing transactions through middleware pipeline")
        
        try:
            # Query relevant transactions
            query = BankTransaction.query
            
            if filter_func:
                transactions = [tx for tx in query.all() if filter_func(tx)]
                logger.info(f"Filtered {len(transactions)} transactions to process")
            else:
                transactions = query.all()
                logger.info(f"Processing all {len(transactions)} transactions")
            
            # Process each transaction through the pipeline
            processed_count = 0
            for transaction in transactions:
                try:
                    transaction_pipeline.process_transaction(transaction)
                    processed_count += 1
                    
                    # Log progress periodically
                    if processed_count % 100 == 0:
                        logger.info(f"Processed {processed_count} of {len(transactions)} transactions")
                        
                except Exception as e:
                    logger.error(f"Error processing transaction {transaction.id}: {str(e)}")
                    logger.error(f"Stack trace: {traceback.format_exc()}")
                    # Continue processing other transactions
            
            # Commit the changes
            logger.info(f"Committing changes for {processed_count} processed transactions")
            db.session.commit()
            
            return len(transactions)
            
        except Exception as e:
            logger.error(f"Error in process_existing_transactions: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_transaction_by_id(transaction_id: int) -> Optional[BankTransaction]:
        """
        Get a transaction by its ID.
        
        Args:
            transaction_id: ID of the transaction to get
            
        Returns:
            The transaction object, or None if not found
        """
        try:
            transaction = BankTransaction.query.get(transaction_id)
            if not transaction:
                logger.warning(f"Transaction with ID {transaction_id} not found")
            return transaction
        except Exception as e:
            logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            return None
    
    @staticmethod
    def update_transaction(
        transaction_id: int, 
        updates: Dict[str, Any],
        apply_middleware: bool = True
    ) -> Optional[BankTransaction]:
        """
        Update a transaction with the given data and optionally process it through middlewares.
        
        Args:
            transaction_id: ID of the transaction to update
            updates: Dictionary of attributes to update
            apply_middleware: Whether to apply the middleware pipeline after updating
            
        Returns:
            The updated transaction, or None if not found
        """
        logger.info(f"Updating transaction {transaction_id}")
        try:
            transaction = BankTransaction.query.get(transaction_id)
            if not transaction:
                logger.warning(f"Transaction with ID {transaction_id} not found for update")
                return None
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(transaction, key):
                    logger.debug(f"Updating transaction {transaction_id} field {key}: {value}")
                    setattr(transaction, key, value)
                else:
                    logger.warning(f"Attempted to update unknown field '{key}' on transaction {transaction_id}")
            
            # Apply middleware if requested
            if apply_middleware:
                logger.debug(f"Applying middleware pipeline to updated transaction {transaction_id}")
                transaction = transaction_pipeline.process_transaction(transaction)
            
            # Save changes
            logger.debug(f"Committing update for transaction {transaction_id}")
            db.session.commit()
            
            return transaction
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            db.session.rollback()
            return None