"""
FDIS Application Factory
Football Data Intelligence System
"""
import os
from flask import Flask, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    from config import config_map
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    login_manager.init_app(app)
    
    from app.routes.auth import init_oauth
    init_oauth(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Create database tables
    with app.app_context():
        from app.models import User, Team, Player, Match, MatchStats, PlayerStats, UploadHistory
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
            
        db.create_all()

    # Register template globals and error handlers
    @app.context_processor
    def inject_template_globals():
        return {
            'request': request,
            'url_for': url_for,
        }

    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Resource not found'}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {'error': 'Internal server error'}, 500

    return app
