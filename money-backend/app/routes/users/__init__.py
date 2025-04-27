from flask import Blueprint, jsonify, request
from flask_cors import CORS
from app.models.db import db
from app.models.user import User

bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

# Enable CORS for this blueprint
CORS(bp)

@bp.route('/', methods=['GET'])
def get_users():
    """
    Get all users for dropdown selection in the frontend.
    Returns a list of users with their IDs and names.
    """
    try:
        users = User.query.all()
        return jsonify({
            "status": "success",
            "data": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                }
                for user in users
            ]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/', methods=['POST'])
def create_user():
    """
    Create a new user.
    Requires name and email in the request body.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('email'):
            return jsonify({
                "status": "error",
                "message": "Name and email are required"
            }), 400
        
        # Check if user with email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                "status": "error",
                "message": "User with this email already exists"
            }), 409
        
        # Create new user
        new_user = User(
            name=data['name'],
            email=data['email']
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "User created successfully",
            "data": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a specific user by ID.
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        return jsonify({
            "status": "success",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update an existing user.
    Requires user_id in the URL path and name and/or email in the request body.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
            
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        # Check email uniqueness if changing email
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({
                    "status": "error",
                    "message": "Email already in use by another user"
                }), 409
        
        # Update fields if provided
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
            
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "User updated successfully",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user by ID.
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "User deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500