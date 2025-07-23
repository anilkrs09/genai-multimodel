from flask import Flask
from .db import get_db_conn
from .routes import bp as routes_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(routes_bp)
    return app

