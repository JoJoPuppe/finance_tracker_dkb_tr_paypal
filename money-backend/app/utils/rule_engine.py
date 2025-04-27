from typing import Dict, Any, List, Tuple, Optional
import logging
from app.models.rule import Rule, RuleCondition
from app.models.transaction import BankTransaction

# Set up logger
logger = logging.getLogger('money_backend.rule_engine')

class RuleEngine:
    @staticmethod
    def evaluate_condition(transaction: BankTransaction, condition: RuleCondition) -> bool:
        """Evaluate a single rule condition against a transaction."""
        field_value = getattr(transaction, condition.field, None)
        if field_value is None:
            return False

        field_value = str(field_value).lower()
        condition_value = str(condition.value).lower()
        logger.debug(f"Evaluating condition: field_value={field_value}, condition_value={condition_value}, operator={condition.operator}")
        if condition.operator == "equals":
            return field_value == condition_value
        elif condition.operator == "contains":
            return condition_value in field_value
        elif condition.operator == "starts_with":
            return field_value.startswith(condition_value)
        elif condition.operator == "ends_with":
            return field_value.endswith(condition_value)
    
        return False

    @staticmethod
    def evaluate_rule(transaction: BankTransaction, rule: Rule) -> bool:
        """Evaluate all conditions of a rule against a transaction."""
        try:
            # Store rule ID safely before any potential detachment issues
            rule_id = rule.id
            
            if not rule.conditions:
                logger.debug(f"Rule {rule_id} has no conditions, skipping")
                return False
            
            # Get the logical operator (default to AND if not specified)
            logical_operator = getattr(rule, 'logical_operator', 'AND')
            logger.debug(f"Evaluating rule {rule_id} with {logical_operator} logic")
            
            # Evaluate conditions based on the logical operator
            if logical_operator == 'AND':
                result = all(
                    RuleEngine.evaluate_condition(transaction, condition)
                    for condition in rule.conditions
                )
            elif logical_operator == 'OR':
                result = any(
                    RuleEngine.evaluate_condition(transaction, condition)
                    for condition in rule.conditions
                )
            else:
                # Default to AND for any other value
                logger.warning(f"Unknown logical operator '{logical_operator}' for rule {rule_id}, defaulting to AND")
                result = all(
                    RuleEngine.evaluate_condition(transaction, condition)
                    for condition in rule.conditions
                )
            
            logger.debug(f"Rule {rule_id} evaluation result: {result}")
            return result
        except Exception as e:
            if "DetachedInstanceError" in str(e) or "is not bound to a Session" in str(e):
                # Don't try to access any attributes on a potentially detached object
                logger.warning(f"Rule is detached from session, skipping evaluation")
                return False
            else:
                # For other errors, log without accessing potentially detached attributes
                logger.error(f"Error evaluating rule: {str(e)}")
                return False

    @staticmethod
    def apply_rules(transaction: BankTransaction, rules: List[Rule]) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Apply a list of rules to a transaction.
        Returns a tuple of (matched, category_id, rule_id) where:
        - matched: True if any rule matched
        - category_id: The category_id from the matched rule, or None if no match
        - rule_id: The ID of the matched rule, or None if no match
        """
        logger.debug(f"Applying {len(rules)} rules to transaction {transaction.id}")
        for rule in rules:
            if RuleEngine.evaluate_rule(transaction, rule):
                logger.info(f"Transaction {transaction.id} matched rule {rule.id}, setting category to {rule.category_id}")
                return True, rule.category_id, rule.id
        logger.debug(f"No rules matched for transaction {transaction.id}")
        return False, None, None