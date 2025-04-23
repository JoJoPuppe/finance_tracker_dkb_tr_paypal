from flask import Blueprint, jsonify, request
from flask_cors import CORS
from app.models.db import db
from app.models.rule import Rule, RuleCondition

bp = Blueprint('rules', __name__, url_prefix='/api/v1/rules')

# Enable CORS for this blueprint
CORS(bp)

@bp.route('/', methods=['GET'])
def get_rules():
    try:
        rules = Rule.query.all()
        return jsonify({
            "status": "success",
            "data": [
                {
                    "id": rule.id,
                    "name": rule.name,
                    "category_id": rule.category_id,
                    "logical_operator": rule.logical_operator,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
                    "conditions": [
                        {
                            "id": cond.id,
                            "field": cond.field,
                            "operator": cond.operator,
                            "value": cond.value,
                            "sequence": cond.sequence
                        }
                        for cond in sorted(rule.conditions, key=lambda x: x.sequence)
                    ]
                }
                for rule in rules
            ]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/', methods=['POST'])
def create_rule():
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['name', 'category_id', 'conditions']):
            return jsonify({
                "status": "error",
                "message": "name, category_id, and conditions are required"
            }), 400

        # Create rule with logical_operator if provided (default is "AND" from model)
        rule = Rule(
            name=data['name'],
            category_id=data['category_id'],
            logical_operator=data.get('logical_operator', 'AND')
        )
        
        for idx, condition_data in enumerate(data['conditions']):
            if not all(key in condition_data for key in ['field', 'operator', 'value']):
                return jsonify({
                    "status": "error",
                    "message": "Each condition must have field, operator, and value"
                }), 400
                
            condition = RuleCondition(
                field=condition_data['field'],
                operator=condition_data['operator'],
                value=condition_data['value'],
                sequence=idx
            )
            rule.conditions.append(condition)
        
        db.session.add(rule)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Rule created successfully",
            "data": {
                "id": rule.id,
                "name": rule.name,
                "category_id": rule.category_id,
                "logical_operator": rule.logical_operator,
                "conditions": [
                    {
                        "id": cond.id,
                        "field": cond.field,
                        "operator": cond.operator,
                        "value": cond.value,
                        "sequence": cond.sequence
                    }
                    for cond in sorted(rule.conditions, key=lambda x: x.sequence)
                ]
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    try:
        # Get the rule to update
        rule = Rule.query.get_or_404(rule_id)
        data = request.get_json()
        
        # Find all transactions affected by this rule
        from app.models.transaction import BankTransaction
        affected_transactions = BankTransaction.query.filter_by(rule_id=rule_id).all()
        affected_count = len(affected_transactions)
        
        # Revert the effects: remove category_id and rule_id from affected transactions
        for transaction in affected_transactions:
            transaction.category_id = None
            transaction.rule_id = None
        
        # Update the rule data
        if 'name' in data:
            rule.name = data['name']
        if 'category_id' in data:
            rule.category_id = data['category_id']
        if 'logical_operator' in data:
            rule.logical_operator = data['logical_operator']
            
        if 'conditions' in data:
            # Remove existing conditions
            for condition in rule.conditions:
                db.session.delete(condition)
            
            # Add new conditions
            for idx, condition_data in enumerate(data['conditions']):
                if not all(key in condition_data for key in ['field', 'operator', 'value']):
                    return jsonify({
                        "status": "error",
                        "message": "Each condition must have field, operator, and value"
                    }), 400
                    
                condition = RuleCondition(
                    field=condition_data['field'],
                    operator=condition_data['operator'],
                    value=condition_data['value'],
                    sequence=idx
                )
                rule.conditions.append(condition)
        
        # Commit the changes to the rule and transaction updates
        db.session.commit()
        
        # Re-apply the updated rule to all transactions (if requested)
        reapply_rule = data.get('reapply_rule', True)  # Default to True
        newly_affected_count = 0
        
        if reapply_rule:
            from app.utils.rule_engine import RuleEngine
            # Get all transactions (or we could limit to previously affected ones)
            all_transactions = BankTransaction.query.all()
            
            for transaction in all_transactions:
                # Apply the updated rule to each transaction
                if RuleEngine.evaluate_rule(transaction, rule):
                    transaction.category_id = rule.category_id
                    transaction.rule_id = rule.id
                    newly_affected_count += 1
            
            # Commit the re-application of rules
            db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Rule updated successfully. {affected_count} previous categorizations reverted, {newly_affected_count} transactions newly categorized.",
            "data": {
                "id": rule.id,
                "name": rule.name,
                "category_id": rule.category_id,
                "logical_operator": rule.logical_operator,
                "conditions": [
                    {
                        "id": cond.id,
                        "field": cond.field,
                        "operator": cond.operator,
                        "value": cond.value,
                        "sequence": cond.sequence
                    }
                    for cond in sorted(rule.conditions, key=lambda x: x.sequence)
                ]
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    try:
        rule = Rule.query.get_or_404(rule_id)
        db.session.delete(rule)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Rule deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/<int:rule_id>', methods=['GET'])
def get_rule(rule_id):
    try:
        rule = Rule.query.get_or_404(rule_id)
        return jsonify({
            "status": "success",
            "data": {
                "id": rule.id,
                "name": rule.name,
                "category_id": rule.category_id,
                "logical_operator": rule.logical_operator,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
                "conditions": [
                    {
                        "id": cond.id,
                        "field": cond.field,
                        "operator": cond.operator,
                        "value": cond.value,
                        "sequence": cond.sequence
                    }
                    for cond in sorted(rule.conditions, key=lambda x: x.sequence)
                ]
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500