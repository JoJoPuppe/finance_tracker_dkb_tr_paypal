from flask import Blueprint, jsonify
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