from flask import Blueprint, jsonify, request, url_for
from datetime import datetime
from sqlalchemy import and_, or_, func, extract
from app.models.db import db
from app.models.transaction import BankTransaction
from app.models.rule import Rule
from app.models.category import Category
from app.utils.rule_engine import RuleEngine
from app.utils.transaction_service import TransactionService
import csv
import hashlib
import logging
import traceback
from flask_cors import CORS

# Set up logger
logger = logging.getLogger("money_backend.routes.transactions")

bp = Blueprint("transactions", __name__, url_prefix="/api/v1/transactions")

# Enable CORS for this blueprint
CORS(bp)


def parse_date(date_str, format="%d.%m.%y"):
    try:
        return datetime.strptime(date_str, format).date()
    except Exception:
        return None


def generate_transaction_hash(
    booking_date, value_date, amount, payee, payer, purpose, transaction_type, iban
):
    """
    Generate a unique hash for a transaction to identify duplicates.
    Combines several fields that together should uniquely identify a transaction.

    Args:
        booking_date: The booking date of the transaction
        value_date: The value date of the transaction
        amount: The transaction amount
        payee: The recipient of the transaction
        payer: The sender of the transaction
        purpose: The purpose/description of the transaction
        transaction_type: The type of transaction
        iban: The IBAN involved

    Returns:
        A unique hash string representing the transaction
    """
    # Convert dates to strings if they're not None, otherwise use empty string
    booking_date_str = booking_date.isoformat() if booking_date else ""
    value_date_str = value_date.isoformat() if value_date else ""

    # Create a string combining all the values
    transaction_str = (
        f"{booking_date_str}|{value_date_str}|{str(amount)}|"
        f"{payee or ''}|{payer or ''}|{purpose or ''}|"
        f"{transaction_type or ''}|{iban or ''}"
    )

    # Generate an MD5 hash of the combined string
    # Using MD5 as it's fast and collision probability is low enough for this use case
    return hashlib.md5(transaction_str.encode("utf-8")).hexdigest()


@bp.route("/", methods=["GET"])
def get_transactions():
    try:
        # Get pagination parameters
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 25, type=int)

        # Start with base query
        query = BankTransaction.query

        # Apply date range filter
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        if start_date:
            start_date = parse_date(start_date, "%Y-%m-%d")
            if start_date:
                query = query.filter(BankTransaction.booking_date >= start_date)
        if end_date:
            end_date = parse_date(end_date, "%Y-%m-%d")
            if end_date:
                query = query.filter(BankTransaction.booking_date <= end_date)

        # Apply amount range filter
        min_amount = request.args.get("min_amount", type=float)
        max_amount = request.args.get("max_amount", type=float)
        if min_amount is not None:
            query = query.filter(BankTransaction.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(BankTransaction.amount <= max_amount)

        # Apply category filter
        category_id = request.args.get("category_id", type=int)
        if category_id is not None:
            query = query.filter(BankTransaction.category_id == category_id)

        # Apply search filter
        search = request.args.get("search")
        if search:
            search = f"%{search}%"
            query = query.filter(
                or_(
                    BankTransaction.payee.ilike(search),
                    BankTransaction.payer.ilike(search),
                    BankTransaction.purpose.ilike(search),
                )
            )

        # Apply sorting
        sort_by = request.args.get("sort_by", "booking_date")
        sort_order = request.args.get("sort_order", "desc")

        if hasattr(BankTransaction, sort_by):
            sort_column = getattr(BankTransaction, sort_by)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # Execute paginated query
        paginated_txs = query.paginate(page=page, per_page=per_page, error_out=False)

        # Prepare pagination metadata
        args = dict(request.args)
        if "page" in args:
            del args["page"]  # Remove page from args to avoid duplication

        next_url = (
            url_for(
                "transactions.get_transactions", page=paginated_txs.next_num, **args
            )
            if paginated_txs.has_next
            else None
        )
        prev_url = (
            url_for(
                "transactions.get_transactions", page=paginated_txs.prev_num, **args
            )
            if paginated_txs.has_prev
            else None
        )

        return jsonify(
            {
                "status": "success",
                "data": [
                    {
                        "id": tx.id,
                        "booking_date": tx.booking_date.strftime("%Y-%m-%d")
                        if tx.booking_date
                        else None,
                        "value_date": tx.value_date.strftime("%Y-%m-%d")
                        if tx.value_date
                        else None,
                        "amount": float(tx.amount) if tx.amount else 0.0,
                        "payee": tx.payee,
                        "payer": tx.payer,
                        "purpose": tx.purpose,
                        "transaction_type": tx.transaction_type,
                        "iban": tx.iban,
                        "creditor_id": tx.creditor_id,
                        "mandate_reference": tx.mandate_reference,
                        "customer_reference": tx.customer_reference,
                        "category_id": tx.category_id,
                        "category_name": tx.category.name if tx.category else None,
                    }
                    for tx in paginated_txs.items
                ],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_pages": paginated_txs.pages,
                    "total_items": paginated_txs.total,
                    "next_url": next_url,
                    "prev_url": prev_url,
                },
            }
        ), 200
    except Exception as e:
        return jsonify(
            {"status": "error", "message": str(e), "error_type": type(e).__name__}
        ), 500


@bp.route("/import", methods=["POST"])
def import_csv():
    logger.info("Starting CSV import process")
    try:
        if "file" not in request.files:
            logger.warning("No file provided in request")
            return jsonify({"status": "error", "message": "No file provided"}), 400

        file = request.files["file"]
        if not file.filename.endswith(".csv"):
            logger.warning(f"Invalid file format: {file.filename}")
            return jsonify(
                {
                    "status": "error",
                    "message": "Invalid file format. Please upload a CSV file",
                }
            ), 400

        logger.debug(f"Processing CSV file: {file.filename}")

        try:
            csv_lines = file.read().decode("utf-8").splitlines()
            logger.debug(f"CSV file read, got {len(csv_lines)} lines")

            if len(csv_lines) < 5:
                logger.error(f"CSV file has too few lines: {len(csv_lines)}")
                return jsonify(
                    {
                        "status": "error",
                        "message": "CSV file format is invalid - too few lines",
                    }
                ), 400

            try:
                own_iban = csv_lines[0].split(";")[1].strip()
                logger.debug(f"Extracted own IBAN: {own_iban}")
            except (IndexError, KeyError) as e:
                logger.error(f"Failed to extract own IBAN from first line: {str(e)}")
                return jsonify(
                    {
                        "status": "error",
                        "message": "CSV format error: Could not extract IBAN from header",
                    }
                ), 400

            try:
                reader = csv.DictReader(csv_lines[4:], delimiter=";")
                logger.debug("CSV DictReader initialized")
            except Exception as e:
                logger.error(f"Failed to create CSV reader: {str(e)}")
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to parse CSV format: {str(e)}",
                    }
                ), 400
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error on CSV file: {str(e)}")
            return jsonify(
                {
                    "status": "error",
                    "message": "File encoding is not UTF-8. Please convert to UTF-8 and try again.",
                }
            ), 400

        # Prepare transaction data list for processing through middleware
        transaction_data_list = []
        row_index = 0

        for row in reader:
            row_index += 1
            try:
                logger.debug(f"Processing row {row_index}")
                if "Betrag (€)" not in row:
                    logger.error(
                        f"Missing 'Betrag (€)' column in row {row_index}: {row}"
                    )
                    return jsonify(
                        {
                            "status": "error",
                            "message": f"CSV format error: Missing 'Betrag (€)' column in row {row_index}",
                        }
                    ), 400

                try:
                    amount_str = (
                        row["Betrag (€)"].replace(".", "").replace(",", ".").strip()
                    )
                    amount = float(amount_str)
                    logger.debug(f"Parsed amount: {amount}")
                except (ValueError, TypeError) as e:
                    logger.error(
                        f"Failed to parse amount in row {row_index}: {row['Betrag (€)']} - {str(e)}"
                    )
                    return jsonify(
                        {
                            "status": "error",
                            "message": f"Invalid amount format in row {row_index}: {row['Betrag (€)']}",
                        }
                    ), 400

                try:
                    booking_date = parse_date(row["Buchungsdatum"])
                    value_date = parse_date(row["Wertstellung"])
                    logger.debug(
                        f"Parsed dates: booking={booking_date}, value={value_date}"
                    )

                    if booking_date is None:
                        logger.warning(
                            f"Could not parse booking date in row {row_index}: {row['Buchungsdatum']}"
                        )
                except KeyError as e:
                    logger.error(f"Missing date column in row {row_index}: {str(e)}")
                    return jsonify(
                        {
                            "status": "error",
                            "message": f"CSV format error: Missing date column {str(e)} in row {row_index}",
                        }
                    ), 400

                payee = row.get("Zahlungsempfänger*in", "")
                payer = row.get("Zahlungspflichtige*r", "")
                purpose = row.get("Verwendungszweck", "")
                booking_date = row.get("Buchungsdatum", "")
                value_date = row.get("Wertstellung", "")
                transaction_type = row.get("Umsatztyp", "")
                iban = own_iban
                counterparty_iban = row.get("IBAN", "")

                # Create transaction data dictionary
                transaction_data = {
                    "booking_date": booking_date,
                    "value_date": value_date,
                    "status": row.get("Status", ""),
                    "payer": payer,
                    "payee": payee,
                    "purpose": purpose,
                    "transaction_type": transaction_type,
                    "iban": iban,
                    "counterparty_iban": counterparty_iban,
                    "amount": amount,
                    "creditor_id": row.get("Gläubiger-ID", ""),
                    "mandate_reference": row.get("Mandatsreferenz", ""),
                    "customer_reference": row.get("Kundenreferenz", ""),
                }

                transaction_data_list.append(transaction_data)
            except Exception as e:
                logger.error(f"Error processing row {row_index}: {str(e)}")
                logger.error(f"Row data: {row}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return jsonify(
                    {
                        "status": "error",
                        "message": f"Error processing row {row_index}: {str(e)}",
                    }
                ), 400

        # Process transactions through middleware pipeline and save them
        logger.info(
            f"Parsed {len(transaction_data_list)} transactions from CSV, now importing through middleware"
        )
        try:
            saved_transactions = TransactionService.import_and_save_transactions(
                transaction_data_list
            )
            logger.info(f"Successfully imported {len(saved_transactions)} transactions")

            return jsonify(
                {
                    "status": "success",
                    "message": f"CSV imported successfully. {len(saved_transactions)} transactions added.",
                }
            ), 201
        except Exception as e:
            logger.error(
                f"Error in TransactionService.import_and_save_transactions: {str(e)}"
            )
            logger.error(f"Stack trace: {traceback.format_exc()}")
            db.session.rollback()
            return jsonify(
                {"status": "error", "message": f"Error saving transactions: {str(e)}"}
            ), 500

    except Exception as e:
        logger.error(f"Unhandled exception in CSV import: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/apply-rules", methods=["POST"])
def apply_rules_to_transactions():
    """Apply rules to all uncategorized transactions using the middleware system."""
    try:
        # Define a filter function to get only uncategorized transactions
        filter_func = lambda tx: tx.category_id is None

        # Process the transactions through the middleware pipeline
        count = TransactionService.process_existing_transactions(filter_func)

        return jsonify(
            {
                "status": "success",
                "message": f"Rules applied successfully. {count} transactions processed.",
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/apply-rule/<int:rule_id>", methods=["POST"])
def apply_specific_rule_to_transactions(rule_id):
    """Apply a specific rule to all transactions, regardless of current categorization."""
    try:
        # Fetch the specific rule
        rule = Rule.query.get_or_404(rule_id)

        # Get all transactions
        transactions = BankTransaction.query.all()

        # Apply the rule to each transaction
        updated_count = 0
        for transaction in transactions:
            # Evaluate the rule against the transaction
            if RuleEngine.evaluate_rule(transaction, rule):
                # If rule matches, update the transaction's category and rule_id
                transaction.category_id = rule.category_id
                transaction.rule_id = rule.id
                updated_count += 1

        if updated_count > 0:
            db.session.commit()

        return jsonify(
            {
                "status": "success",
                "message": f"Rule '{rule.name}' applied successfully. {updated_count} transactions categorized.",
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/revert-rule/<int:rule_id>", methods=["POST"])
def revert_rule_application(rule_id):
    """Revert the effects of a specific rule on all transactions it was applied to."""
    try:
        # Find all transactions where this rule was applied
        transactions = BankTransaction.query.filter_by(rule_id=rule_id).all()

        # Count affected transactions
        affected_count = len(transactions)

        # Revert the effects: remove category_id and rule_id
        for transaction in transactions:
            transaction.category_id = None
            transaction.rule_id = None

        # Commit changes if any
        if affected_count > 0:
            db.session.commit()

        return jsonify(
            {
                "status": "success",
                "message": f"Rule effects reverted successfully. {affected_count} transactions were reset.",
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/<int:transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    try:
        tx = BankTransaction.query.get_or_404(transaction_id)
        return jsonify(
            {
                "status": "success",
                "data": {
                    "id": tx.id,
                    "booking_date": tx.booking_date.strftime("%Y-%m-%d")
                    if tx.booking_date
                    else None,
                    "value_date": tx.value_date.strftime("%Y-%m-%d")
                    if tx.value_date
                    else None,
                    "amount": float(tx.amount) if tx.amount else 0.0,
                    "payee": tx.payee,
                    "payer": tx.payer,
                    "purpose": tx.purpose,
                    "transaction_type": tx.transaction_type,
                    "iban": tx.iban,
                    "creditor_id": tx.creditor_id,
                    "mandate_reference": tx.mandate_reference,
                    "customer_reference": tx.customer_reference,
                    "category_id": tx.category_id,
                    "category_name": tx.category.name if tx.category else None,
                    "transaction_hash": tx.transaction_hash,
                },
            }
        ), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/<int:transaction_id>/category", methods=["PUT"])
def update_transaction_category(transaction_id):
    try:
        tx = BankTransaction.query.get_or_404(transaction_id)
        data = request.get_json()

        if "category_id" not in data:
            return jsonify(
                {"status": "error", "message": "category_id is required"}
            ), 400

        tx.category_id = data["category_id"]
        db.session.commit()

        return jsonify(
            {
                "status": "success",
                "message": "Transaction category updated successfully",
                "data": {
                    "id": tx.id,
                    "category_id": tx.category_id,
                    "category_name": tx.category.name if tx.category else None,
                },
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/statistics", methods=["GET"])
def get_statistics():
    try:
        # Get date range from query parameters or default to current month
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = BankTransaction.query

        if start_date:
            start_date = parse_date(start_date, "%Y-%m-%d")
            if start_date:
                query = query.filter(BankTransaction.booking_date >= start_date)
        if end_date:
            end_date = parse_date(end_date, "%Y-%m-%d")
            if end_date:
                query = query.filter(BankTransaction.booking_date <= end_date)

        # Calculate overall statistics
        stats = (
            db.session.query(
                func.sum(BankTransaction.amount).label("total_amount"),
                func.count().label("total_transactions"),
                func.avg(BankTransaction.amount).label("average_amount"),
                func.min(BankTransaction.amount).label("min_amount"),
                func.max(BankTransaction.amount).label("max_amount"),
            )
            .filter(query.whereclause)
            .first()
        )

        # Calculate category breakdown
        category_stats = (
            db.session.query(
                Category.id,
                Category.name,
                func.count().label("transaction_count"),
                func.sum(BankTransaction.amount).label("total_amount"),
            )
            .join(BankTransaction, BankTransaction.category_id == Category.id)
            .filter(query.whereclause if query.whereclause is not None else True)
            .group_by(Category.id)
            .all()
        )

        # Calculate monthly trends
        monthly_stats = (
            db.session.query(
                extract("year", BankTransaction.booking_date).label("year"),
                extract("month", BankTransaction.booking_date).label("month"),
                func.sum(BankTransaction.amount).label("total_amount"),
                func.count().label("transaction_count"),
            )
            .filter(query.whereclause if query.whereclause is not None else True)
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "summary": {
                        "total_amount": float(stats.total_amount)
                        if stats.total_amount
                        else 0.0,
                        "total_transactions": stats.total_transactions,
                        "average_amount": float(stats.average_amount)
                        if stats.average_amount
                        else 0.0,
                        "min_amount": float(stats.min_amount)
                        if stats.min_amount
                        else 0.0,
                        "max_amount": float(stats.max_amount)
                        if stats.max_amount
                        else 0.0,
                    },
                    "categories": [
                        {
                            "id": stat.id,
                            "name": stat.name,
                            "transaction_count": stat.transaction_count,
                            "total_amount": float(stat.total_amount)
                            if stat.total_amount
                            else 0.0,
                        }
                        for stat in category_stats
                    ],
                    "monthly_trends": [
                        {
                            "year": int(stat.year),
                            "month": int(stat.month),
                            "total_amount": float(stat.total_amount)
                            if stat.total_amount
                            else 0.0,
                            "transaction_count": stat.transaction_count,
                        }
                        for stat in monthly_stats
                    ],
                },
            }
        ), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/category-summary", methods=["GET"])
def get_category_summary():
    try:
        # Get statistics for each category
        category_stats = (
            db.session.query(
                Category.id,
                Category.name,
                Category.parent_id,
                func.count(BankTransaction.id).label("transaction_count"),
                func.sum(BankTransaction.amount).label("total_amount"),
                func.avg(BankTransaction.amount).label("average_amount"),
            )
            .outerjoin(BankTransaction, BankTransaction.category_id == Category.id)
            .group_by(Category.id)
            .all()
        )

        # Organize categories into a hierarchy
        categories_dict = {}
        root_categories = []

        for stat in category_stats:
            category_data = {
                "id": stat.id,
                "name": stat.name,
                "transaction_count": stat.transaction_count,
                "total_amount": float(stat.total_amount) if stat.total_amount else 0.0,
                "average_amount": float(stat.average_amount)
                if stat.average_amount
                else 0.0,
                "subcategories": [],
            }
            categories_dict[stat.id] = category_data

            if stat.parent_id is None:
                root_categories.append(category_data)
            else:
                parent = categories_dict.get(stat.parent_id)
                if parent:
                    parent["subcategories"].append(category_data)

        return jsonify({"status": "success", "data": root_categories}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/search-by-column", methods=["GET"])
def search_transactions_by_column():
    try:
        column_name = request.args.get("column")
        search_value = request.args.get("value")

        if not column_name or not search_value:
            return jsonify(
                {
                    "status": "error",
                    "message": "Both column and value parameters are required",
                }
            ), 400

        # Validate that the column exists in the BankTransaction model
        if not hasattr(BankTransaction, column_name):
            return jsonify(
                {
                    "status": "error",
                    "message": f"Column '{column_name}' does not exist in BankTransaction model",
                }
            ), 400

        # Get the column object
        column = getattr(BankTransaction, column_name)

        # Only string columns can be searched with LIKE
        if not isinstance(column.type, db.String) and not isinstance(
            column.type, db.Text
        ):
            return jsonify(
                {
                    "status": "error",
                    "message": f"Column '{column_name}' is not a string type and cannot be searched with partial matching",
                }
            ), 400

        # Build the query with case-insensitive LIKE filter
        query = BankTransaction.query.filter(column.ilike(f"%{search_value}%")).limit(5)

        # Execute the query
        transactions = query.all()

        return jsonify(
            {
                "status": "success",
                "data": [
                    {
                        "id": tx.id,
                        "booking_date": tx.booking_date.strftime("%Y-%m-%d")
                        if tx.booking_date
                        else None,
                        "value_date": tx.value_date.strftime("%Y-%m-%d")
                        if tx.value_date
                        else None,
                        "amount": float(tx.amount) if tx.amount else 0.0,
                        "payee": tx.payee,
                        "payer": tx.payer,
                        "purpose": tx.purpose,
                        "transaction_type": tx.transaction_type,
                        "iban": tx.iban,
                        "category_id": tx.category_id,
                        "category_name": tx.category.name if tx.category else None,
                        "transaction_hash": tx.transaction_hash,
                    }
                    for tx in transactions
                ],
                "count": len(transactions),
            }
        ), 200
    except Exception as e:
        return jsonify(
            {"status": "error", "message": str(e), "error_type": type(e).__name__}
        ), 500


@bp.route("/columns", methods=["GET"])
def get_transaction_columns():
    try:
        # Get all columns from BankTransaction model
        columns = BankTransaction.__table__.columns.keys()

        # Return the list of column names
        return jsonify({"status": "success", "data": {"columns": list(columns)}}), 200
    except Exception as e:
        return jsonify(
            {"status": "error", "message": str(e), "error_type": type(e).__name__}
        ), 500


@bp.route("/by-category/<int:category_id>", methods=["GET"])
def get_transactions_by_category(category_id):
    try:
        # Get pagination parameters
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 25, type=int)

        # Get all transactions with the specified category ID
        query = BankTransaction.query.filter_by(category_id=category_id)

        # Apply sorting
        sort_by = request.args.get("sort_by", "booking_date")
        sort_order = request.args.get("sort_order", "desc")

        if hasattr(BankTransaction, sort_by):
            sort_column = getattr(BankTransaction, sort_by)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # Execute paginated query
        paginated_txs = query.paginate(page=page, per_page=per_page, error_out=False)

        # Get category info
        category = Category.query.get_or_404(category_id)

        # Prepare pagination metadata
        args = dict(request.args)
        if "page" in args:
            del args["page"]  # Remove page from args to avoid duplication

        next_url = (
            url_for(
                "transactions.get_transactions_by_category",
                category_id=category_id,
                page=paginated_txs.next_num,
                **args,
            )
            if paginated_txs.has_next
            else None
        )
        prev_url = (
            url_for(
                "transactions.get_transactions_by_category",
                category_id=category_id,
                page=paginated_txs.prev_num,
                **args,
            )
            if paginated_txs.has_prev
            else None
        )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description
                        if hasattr(category, "description")
                        else None,
                    },
                    "transactions": [
                        {
                            "id": tx.id,
                            "booking_date": tx.booking_date.strftime("%Y-%m-%d")
                            if tx.booking_date
                            else None,
                            "value_date": tx.value_date.strftime("%Y-%m-%d")
                            if tx.value_date
                            else None,
                            "amount": float(tx.amount) if tx.amount else 0.0,
                            "payee": tx.payee,
                            "payer": tx.payer,
                            "purpose": tx.purpose,
                            "transaction_type": tx.transaction_type,
                            "iban": tx.iban,
                            "creditor_id": tx.creditor_id,
                            "mandate_reference": tx.mandate_reference,
                            "customer_reference": tx.customer_reference,
                            "transaction_hash": tx.transaction_hash,
                        }
                        for tx in paginated_txs.items
                    ],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total_pages": paginated_txs.pages,
                        "total_items": paginated_txs.total,
                        "next_url": next_url,
                        "prev_url": prev_url,
                    },
                },
            }
        ), 200
    except Exception as e:
        return jsonify(
            {"status": "error", "message": str(e), "error_type": type(e).__name__}
        ), 500


@bp.route("/uncategorized", methods=["GET"])
def get_uncategorized_transactions():
    try:
        # Get pagination parameters
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 25, type=int)

        # Get all transactions with no category
        query = BankTransaction.query.filter_by(category_id=None)

        # Apply sorting
        sort_by = request.args.get("sort_by", "booking_date")
        sort_order = request.args.get("sort_order", "desc")

        if hasattr(BankTransaction, sort_by):
            sort_column = getattr(BankTransaction, sort_by)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # Execute paginated query
        paginated_txs = query.paginate(page=page, per_page=per_page, error_out=False)

        # Prepare pagination metadata
        args = dict(request.args)
        if "page" in args:
            del args["page"]  # Remove page from args to avoid duplication

        next_url = (
            url_for(
                "transactions.get_uncategorized_transactions",
                page=paginated_txs.next_num,
                **args,
            )
            if paginated_txs.has_next
            else None
        )
        prev_url = (
            url_for(
                "transactions.get_uncategorized_transactions",
                page=paginated_txs.prev_num,
                **args,
            )
            if paginated_txs.has_prev
            else None
        )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "category": {
                        "id": None,
                        "name": "Uncategorized",
                        "description": "Transactions without assigned category",
                    },
                    "transactions": [
                        {
                            "id": tx.id,
                            "booking_date": tx.booking_date.strftime("%Y-%m-%d")
                            if tx.booking_date
                            else None,
                            "value_date": tx.value_date.strftime("%Y-%m-%d")
                            if tx.value_date
                            else None,
                            "amount": float(tx.amount) if tx.amount else 0.0,
                            "payee": tx.payee,
                            "payer": tx.payer,
                            "purpose": tx.purpose,
                            "transaction_type": tx.transaction_type,
                            "iban": tx.iban,
                            "creditor_id": tx.creditor_id,
                            "mandate_reference": tx.mandate_reference,
                            "customer_reference": tx.customer_reference,
                            "transaction_hash": tx.transaction_hash,
                        }
                        for tx in paginated_txs.items
                    ],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total_pages": paginated_txs.pages,
                        "total_items": paginated_txs.total,
                        "next_url": next_url,
                        "prev_url": prev_url,
                    },
                },
            }
        ), 200
    except Exception as e:
        return jsonify(
            {"status": "error", "message": str(e), "error_type": type(e).__name__}
        ), 500


@bp.route("/search", methods=["GET"])
def search_transactions():
    try:
        # Get search term and pagination parameters
        search_term = request.args.get("q", "")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 25, type=int)
        category_id = request.args.get("category_id")

        # Validate search term
        if not search_term or len(search_term) < 2:
            return jsonify(
                {
                    "status": "error",
                    "message": "Search term must be at least 2 characters",
                }
            ), 400

        # Start building the query
        query = BankTransaction.query

        # Add category filter if provided
        if category_id:
            if category_id == "no-category":
                query = query.filter(BankTransaction.category_id == None)
            elif category_id.isdigit():
                query = query.filter(BankTransaction.category_id == int(category_id))

        # Add fuzzy search across multiple columns
        search_term = f"%{search_term}%"
        query = query.filter(
            or_(
                BankTransaction.payee.ilike(search_term),
                BankTransaction.payer.ilike(search_term),
                BankTransaction.purpose.ilike(search_term),
            )
        )

        # Apply sorting - newest transactions first by default
        query = query.order_by(BankTransaction.booking_date.desc())

        # Execute paginated query
        paginated_txs = query.paginate(page=page, per_page=per_page, error_out=False)

        # Prepare pagination metadata
        args = dict(request.args)
        if "page" in args:
            del args["page"]  # Remove page from args to avoid duplication

        next_url = (
            url_for(
                "transactions.search_transactions", page=paginated_txs.next_num, **args
            )
            if paginated_txs.has_next
            else None
        )
        prev_url = (
            url_for(
                "transactions.search_transactions", page=paginated_txs.prev_num, **args
            )
            if paginated_txs.has_prev
            else None
        )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "transactions": [
                        {
                            "id": tx.id,
                            "booking_date": tx.booking_date.strftime("%Y-%m-%d")
                            if tx.booking_date
                            else None,
                            "value_date": tx.value_date.strftime("%Y-%m-%d")
                            if tx.value_date
                            else None,
                            "amount": float(tx.amount) if tx.amount else 0.0,
                            "payee": tx.payee,
                            "payer": tx.payer,
                            "purpose": tx.purpose,
                            "transaction_type": tx.transaction_type,
                            "iban": tx.iban,
                            "creditor_id": tx.creditor_id,
                            "mandate_reference": tx.mandate_reference,
                            "customer_reference": tx.customer_reference,
                            "category_id": tx.category_id,
                            "category_name": tx.category.name if tx.category else None,
                            "transaction_hash": tx.transaction_hash,
                        }
                        for tx in paginated_txs.items
                    ],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total_pages": paginated_txs.pages,
                        "total_items": paginated_txs.total,
                        "next_url": next_url,
                        "prev_url": prev_url,
                    },
                },
            }
        ), 200
    except Exception as e:
        return jsonify(
            {"status": "error", "message": str(e), "error_type": type(e).__name__}
        ), 500
