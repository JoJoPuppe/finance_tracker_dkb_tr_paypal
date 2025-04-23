from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        """Handle all HTTP errors."""
        response = {
            "status": "error",
            "message": e.description,
            "error_type": e.__class__.__name__,
            "code": e.code
        }
        return jsonify(response), e.code

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(e):
        """Handle database errors."""
        if isinstance(e, IntegrityError):
            message = "Database integrity error. This might be due to duplicate data or invalid relationships."
        else:
            message = "An unexpected database error occurred."
        
        response = {
            "status": "error",
            "message": message,
            "error_type": e.__class__.__name__,
            "code": 500
        }
        return jsonify(response), 500

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        """Handle any unhandled exceptions."""
        response = {
            "status": "error",
            "message": "An unexpected error occurred.",
            "error_type": e.__class__.__name__,
            "code": 500
        }
        return jsonify(response), 500