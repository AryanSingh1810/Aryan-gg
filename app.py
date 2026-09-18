import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from config import config_by_name, Config
from models import db
from routes import main_bp, game_bp, auth_bp, song_bp
from sockets import register_socket_handlers

socketio = SocketIO()

def create_app(config_name: str = "default") -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_obj)

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins=Config.CORS_ALLOWED_ORIGINS,
        async_mode=Config.SOCKETIO_ASYNC_MODE,
        ping_timeout=30,
        ping_interval=10
    )

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(song_bp)

    # Register Socket.IO handlers
    register_socket_handlers(socketio)

    # Ensure tables exist
    with app.app_context():
        db.create_all()

    return app

app = create_app(os.getenv("FLASK_ENV", "default"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f">> Starting DRAW & GUESS (D&G) server at http://localhost:{port}")
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=Config.DEBUG if hasattr(Config, "DEBUG") else True,
        allow_unsafe_werkzeug=True
    )
