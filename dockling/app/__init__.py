from flask import Flask
from .db import conn  # Ensure DB connects early

def create_app():
    app = Flask(__name__)

    from .uploadfile import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

