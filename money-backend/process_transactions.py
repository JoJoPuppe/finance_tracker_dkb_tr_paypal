#!/usr/bin/env python
"""
Transaction Processing CLI

This script provides command-line utilities for processing bank transactions
using the middleware pipeline.
"""
import argparse
import sys
import datetime
import logging
import os
from typing import Optional, List, Dict, Any
from flask import current_app
from app import create_app
from app.models.transaction import BankTransaction
from app.utils.transaction_service import TransactionService
from app.utils.transaction_middleware import transaction_pipeline
from app.utils.transaction_middlewares import (
    DataCleaningMiddleware,
    ApplyRulesMiddleware,
    InternalTransferDetectionMiddleware,
    TransactionHashMiddleware,
    PatternExtractionMiddleware
)

# Set up logger
logger = logging.getLogger('money_backend.process_transactions')

def setup_logging():
    """Set up logging if run as standalone script"""
    if not logger.handlers:
        # Create logger
        logger.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Create file handler for logging to a file
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'money_backend_{datetime.datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Create console handler for logging to stdout
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

def parse_date(date_string: str) -> Optional[datetime.date]:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None

def process_transactions(args):
    """Process existing transactions based on command line arguments."""
    app = create_app()
    
    with app.app_context():
        # Build filter function based on arguments
        filters = []
        
        if args.start_date:
            start_date = parse_date(args.start_date)
            if start_date:
                filters.append(lambda tx: tx.booking_date >= start_date)
                
        if args.end_date:
            end_date = parse_date(args.end_date)
            if end_date:
                filters.append(lambda tx: tx.booking_date <= end_date)
                
        if args.category_id:
            if args.category_id == 'null':
                filters.append(lambda tx: tx.category_id is None)
            elif args.category_id == 'not_null':
                filters.append(lambda tx: tx.category_id is not None)
            else:
                try:
                    category_id = int(args.category_id)
                    filters.append(lambda tx: tx.category_id == category_id)
                except ValueError:
                    logger.error(f"Invalid category ID: {args.category_id}")
                    return
        
        if args.min_amount:
            try:
                min_amount = float(args.min_amount)
                filters.append(lambda tx: tx.amount >= min_amount)
            except ValueError:
                logger.error(f"Invalid min amount: {args.min_amount}")
                return
                
        if args.max_amount:
            try:
                max_amount = float(args.max_amount)
                filters.append(lambda tx: tx.amount <= max_amount)
            except ValueError:
                logger.error(f"Invalid max amount: {args.max_amount}")
                return
                
        # Combine filters with AND logic
        filter_func = None
        if filters:
            filter_func = lambda tx: all(f(tx) for f in filters)
        
        # Configure custom middleware if needed
        if args.only_rules:
            # Reset middleware pipeline to only include rule application
            transaction_pipeline.middlewares = [ApplyRulesMiddleware()]
            logger.info("Processing transactions with rules middleware only")
            
        if args.only_transfers:
            # Reset middleware pipeline to only include internal transfer detection
            transaction_pipeline.middlewares = [InternalTransferDetectionMiddleware()]
            logger.info("Processing transactions with internal transfer detection middleware only")
            
        if args.only_cleaning:
            # Reset middleware pipeline to only include data cleaning
            transaction_pipeline.middlewares = [DataCleaningMiddleware()]
            logger.info("Processing transactions with data cleaning middleware only")
            
        if args.only_hashing:
            # Reset middleware pipeline to only include transaction hashing
            transaction_pipeline.middlewares = [TransactionHashMiddleware()]
            logger.info("Processing transactions with transaction hashing middleware only")

        # Process transactions
        logger.info("Starting transaction processing...")
        count = TransactionService.process_existing_transactions(filter_func)
        logger.info(f"Processed {count} transactions")

def main():
    setup_logging()
    logger.info("Transaction processing CLI started")
    
    parser = argparse.ArgumentParser(description='Process bank transactions using middleware.')
    
    # Main subcommand parsers
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process existing transactions')
    
    # Filter options
    process_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    process_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    process_parser.add_argument('--category-id', help='Filter by category ID (use "null" for uncategorized, "not_null" for categorized)')
    process_parser.add_argument('--min-amount', help='Minimum transaction amount')
    process_parser.add_argument('--max-amount', help='Maximum transaction amount')
    
    # Middleware options
    process_parser.add_argument('--only-rules', action='store_true', help='Only apply categorization rules')
    process_parser.add_argument('--only-transfers', action='store_true', help='Only detect internal transfers')
    process_parser.add_argument('--only-cleaning', action='store_true', help='Only perform data cleaning')
    process_parser.add_argument('--only-hashing', action='store_true', help='Only generate transaction hashes')
    
    args = parser.parse_args()
    
    if args.command == 'process':
        process_transactions(args)
    else:
        # Instead of just printing help, log it too
        logger.info("No command specified, showing help")
        parser.print_help()

if __name__ == '__main__':
    main()