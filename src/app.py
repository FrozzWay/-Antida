from flask import Flask
from src.database import db

from src.blueprints.register import bp as reg_bp

app = Flask(__name__)

db.init_app(app)

app.register_blueprint(reg_bp)
