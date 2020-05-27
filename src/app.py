from flask import Flask
from src.database import db

from src.blueprints.register import bp as reg_bp
from src.blueprints.auth import bp as auth_bp

app = Flask(__name__)

db.init_app(app)

app.register_blueprint(reg_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")

app.secret_key = b'_5#y2L"F4ffQ8z\n\xec]/k'
