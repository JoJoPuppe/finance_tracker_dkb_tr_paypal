from flask import Blueprint, jsonify, request
from flask_cors import CORS
from app.models.db import db
from app.models.category import Category

bp = Blueprint('categories', __name__, url_prefix='/api/v1/categories')

# Enable CORS for this blueprint
CORS(bp)

@bp.route('/', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.all()
        return jsonify({
            "status": "success",
            "data": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "parent_id": cat.parent_id,
                    "created_at": cat.created_at.isoformat() if cat.created_at else None,
                    "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
                    "subcategories": [
                        {"id": sub.id, "name": sub.name}
                        for sub in cat.subcategories
                    ] if cat.subcategories else []
                }
                for cat in categories
            ]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/', methods=['POST'])
def create_category():
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({
                "status": "error",
                "message": "name is required"
            }), 400

        category = Category(
            name=data['name'],
            parent_id=data.get('parent_id')  # Optional parent_id
        )
        
        db.session.add(category)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Category created successfully",
            "data": {
                "id": category.id,
                "name": category.name,
                "parent_id": category.parent_id
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        
        if 'name' in data:
            category.name = data['name']
        if 'parent_id' in data:
            category.parent_id = data['parent_id']
            
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Category updated successfully",
            "data": {
                "id": category.id,
                "name": category.name,
                "parent_id": category.parent_id
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        
        # Check if category has transactions
        if category.transactions:
            return jsonify({
                "status": "error",
                "message": "Cannot delete category that has transactions"
            }), 400
            
        # Check if category has subcategories
        if category.subcategories:
            return jsonify({
                "status": "error",
                "message": "Cannot delete category that has subcategories"
            }), 400

        db.session.delete(category)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Category deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        return jsonify({
            "status": "success",
            "data": {
                "id": category.id,
                "name": category.name,
                "parent_id": category.parent_id,
                "created_at": category.created_at.isoformat() if category.created_at else None,
                "updated_at": category.updated_at.isoformat() if category.updated_at else None,
                "subcategories": [
                    {"id": sub.id, "name": sub.name}
                    for sub in category.subcategories
                ] if category.subcategories else [],
                "transaction_count": len(category.transactions)
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500