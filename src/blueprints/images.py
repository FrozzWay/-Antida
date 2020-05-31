import src.auth as a
import os
from flask import (
 request, Blueprint, current_app, jsonify, send_from_directory
)
from flask.views import MethodView
from werkzeug.utils import secure_filename

bp = Blueprint('image', __name__)


class ImageView(MethodView):
    @a.seller_auth_required
    def post(self, user_id, seller_id):
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            upload_path = os.path.join(upload_folder, filename)
            file.save(upload_path)
            response = {
                "url": f'http://{request.host}/images/{filename}'
            }
            return jsonify(response), 200
        return '', 403

    def get(self, name):
        filepath = os.path.join(os.getcwd(), 'images')
        return send_from_directory(filepath, name)



bp.add_url_rule('/images', view_func=ImageView.as_view('images'))
bp.add_url_rule('/images/<name>', view_func=ImageView.as_view('imagesf'))