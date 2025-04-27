from flask import Flask, jsonify
from flask_cors import CORS
from .config.config import Config
from .models.db import db, migrate
from .utils.error_handlers import register_error_handlers
from .utils.middleware_config import configure_transaction_middlewares

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Don't enforce trailing slashes on URLs
    app.url_map.strict_slashes = False
    
    # Initialize extensions
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",  # SvelteKit dev server
                "http://localhost:8080",  # Vue CLI default
                "http://localhost:3000",  # Common dev port
                "http://127.0.0.1:5173",  # Vite default
                "http://127.0.0.1:8080",  # Alternative localhost
                "http://127.0.0.1:3000",  # Alternative localhost
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints with v1 prefix
    from .routes.transactions import bp as transactions_bp
    from .routes.categories import bp as categories_bp
    from .routes.rules import bp as rules_bp
    from .routes.users import bp as users_bp
    from .routes.bank_accounts import bp as bank_accounts_bp
    
    app.register_blueprint(transactions_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(bank_accounts_bp)
    
    # Create alternative routes for frontend compatibility
    from flask import Blueprint

    # Create new blueprints with the same views but different prefixes
    def create_alt_blueprint(original_bp, new_prefix, name_suffix):
        alt_bp = Blueprint(
            f"{original_bp.name}_{name_suffix}",
            original_bp.import_name,
            url_prefix=new_prefix
        )
        
        # Copy all the routes from the original blueprint
        for deferred_func in original_bp.deferred_functions:
            alt_bp.deferred_functions.append(deferred_func)
            
        return alt_bp

    # Create alternative blueprints
    transactions_alt = create_alt_blueprint(transactions_bp, '/api/transactions', 'alt')
    categories_alt = create_alt_blueprint(categories_bp, '/api/categories', 'alt')
    rules_alt = create_alt_blueprint(rules_bp, '/api/rules', 'alt')
    users_alt = create_alt_blueprint(users_bp, '/api/users', 'alt')
    bank_accounts_alt = create_alt_blueprint(bank_accounts_bp, '/api/bank_accounts', 'alt')
    
    # Register alternative blueprints
    app.register_blueprint(transactions_alt)
    app.register_blueprint(categories_alt)
    app.register_blueprint(rules_alt)
    app.register_blueprint(users_alt)
    app.register_blueprint(bank_accounts_alt)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure transaction middleware pipeline
    with app.app_context():
        configure_transaction_middlewares()
    
    @app.route("/api/v1")
    def index():
        """API status endpoint"""
        return jsonify({
            "status": "success",
            "message": "Finance dashboard API v1",
            "version": "1.0.0"
        })
    
    @app.route("/api/healthcheck")
    def healthcheck():
        """Health check endpoint for monitoring"""
        return jsonify({
            "status": "success",
            "message": "Service is healthy"
        })
    
    return app