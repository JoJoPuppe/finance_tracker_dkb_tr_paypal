from flask import Blueprint, jsonify, request
from flask_cors import CORS
from app.models.db import db
from app.models.bank_account import BankAccount
from app.models.user import User

bp = Blueprint('bank_accounts', __name__, url_prefix='/api/v1/bank_accounts')

# Enable CORS for this blueprint
CORS(bp)

@bp.route('/', methods=['GET'])
def get_bank_accounts():
    """
    Get all bank accounts with their associated users.
    """
    try:
        bank_accounts = BankAccount.query.all()
        return jsonify({
            "status": "success",
            "data": [
                {
                    "id": account.id,
                    "iban": account.iban,
                    "name": account.name,
                    "description": account.description,
                    "user": {
                        "id": account.user.id,
                        "name": account.user.name,
                        "email": account.user.email
                    } if account.user else None,
                    "created_at": account.created_at.isoformat() if account.created_at else None,
                    "updated_at": account.updated_at.isoformat() if account.updated_at else None
                }
                for account in bank_accounts
            ]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:account_id>', methods=['GET'])
def get_bank_account(account_id):
    """
    Get a specific bank account by ID with its associated user.
    """
    try:
        account = BankAccount.query.get(account_id)
        if not account:
            return jsonify({"status": "error", "message": "Bank account not found"}), 404
            
        return jsonify({
            "status": "success",
            "data": {
                "id": account.id,
                "iban": account.iban,
                "name": account.name,
                "description": account.description,
                "user": {
                    "id": account.user.id,
                    "name": account.user.name,
                    "email": account.user.email
                } if account.user else None,
                "created_at": account.created_at.isoformat() if account.created_at else None,
                "updated_at": account.updated_at.isoformat() if account.updated_at else None
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/', methods=['POST'])
def create_bank_account():
    """
    Create a new bank account.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'iban' not in data:
            return jsonify({"status": "error", "message": "IBAN is required"}), 400
        if 'name' not in data:
            return jsonify({"status": "error", "message": "Name is required"}), 400
        if 'user_id' not in data:
            return jsonify({"status": "error", "message": "User ID is required"}), 400
            
        # Check if the user exists
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404
            
        # Check if IBAN already exists
        existing_account = BankAccount.query.filter_by(iban=data['iban']).first()
        if existing_account:
            return jsonify({"status": "error", "message": "Bank account with this IBAN already exists"}), 409

        # Create new bank account
        bank_account = BankAccount(
            iban=data['iban'],
            name=data['name'],
            description=data.get('description'),
            user_id=data['user_id']
        )
        
        db.session.add(bank_account)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Bank account created successfully",
            "data": {
                "id": bank_account.id,
                "iban": bank_account.iban,
                "name": bank_account.name,
                "description": bank_account.description,
                "user_id": bank_account.user_id
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:account_id>', methods=['PUT'])
def update_bank_account(account_id):
    """
    Update a bank account by ID.
    """
    try:
        account = BankAccount.query.get(account_id)
        if not account:
            return jsonify({"status": "error", "message": "Bank account not found"}), 404
            
        data = request.get_json()
        
        # Update fields if provided in the request
        if 'name' in data:
            account.name = data['name']
        if 'description' in data:
            account.description = data['description']
        if 'user_id' in data:
            # Check if the user exists
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify({"status": "error", "message": "User not found"}), 404
            account.user_id = data['user_id']
        
        # IBAN updates should be handled carefully as it's an identifier
        if 'iban' in data and data['iban'] != account.iban:
            # Check if new IBAN already exists
            existing_account = BankAccount.query.filter_by(iban=data['iban']).first()
            if existing_account and existing_account.id != account_id:
                return jsonify({"status": "error", "message": "Bank account with this IBAN already exists"}), 409
            account.iban = data['iban']
            
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Bank account updated successfully",
            "data": {
                "id": account.id,
                "iban": account.iban,
                "name": account.name,
                "description": account.description,
                "user_id": account.user_id
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:account_id>', methods=['DELETE'])
def delete_bank_account(account_id):
    """
    Delete a bank account by ID.
    """
    try:
        account = BankAccount.query.get(account_id)
        if not account:
            return jsonify({"status": "error", "message": "Bank account not found"}), 404
        
        # Check if there are transactions associated with this account
        if account.transactions and len(account.transactions) > 0:
            return jsonify({
                "status": "error", 
                "message": "Cannot delete account with associated transactions"
            }), 400
            
        db.session.delete(account)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Bank account deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_bank_accounts(user_id):
    """
    Get all bank accounts for a specific user.
    """
    try:
        # Check if the user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404
            
        bank_accounts = BankAccount.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            "status": "success",
            "data": [
                {
                    "id": account.id,
                    "iban": account.iban,
                    "name": account.name,
                    "description": account.description,
                    "created_at": account.created_at.isoformat() if account.created_at else None,
                    "updated_at": account.updated_at.isoformat() if account.updated_at else None
                }
                for account in bank_accounts
            ]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500