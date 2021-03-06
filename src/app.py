from flask import Flask
from src.database import db
import os

from src.blueprints.users import bp as users_bp
from src.blueprints.auth import bp as auth_bp
from src.blueprints.cities import bp as city_bp
from src.blueprints.colors import bp as color_bp
from src.blueprints.ads import bp as ads_bp
from src.blueprints.images import bp as images_bp

app = Flask(__name__)

db.init_app(app)

app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(city_bp)
app.register_blueprint(color_bp)
app.register_blueprint(ads_bp)
app.register_blueprint(images_bp)

app.secret_key = b'_5#y2L"F4ffQ8z\n\xec]/k'

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'images')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


