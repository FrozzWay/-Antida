from flask import (
Blueprint, session, request, jsonify
)

from src.database import db
from flask.views import MethodView
import src.auth as a

bp = Blueprint('colors', __name__)


class ColorsView(MethodView):
    @a.seller_auth_required
    def get(self, user_id, seller_id):
        con = db.connection
        cursor = con.execute(
            'SELECT * FROM color'
        )
        colors = [dict(row) for row in cursor.fetchall()]
        return jsonify(colors), 200

    @a.seller_auth_required
    def post(self, user_id, seller_id):
        con = db.connection
        cursor = con.cursor()

        request_json = request.json
        name = request_json.get('name')
        hex = request_json.get('hex')

        try:
            cursor.execute('INSERT INTO color (name, hex) VALUES (?, ?)', (name, hex))
            con.commit()

            color_id = cursor.lastrowid
            print(color_id)

            response = {
                "id": color_id,
                "name": name,
                "hex": hex
            }

            return jsonify(response), 200
        except:
            return {"error": "hex is not unique"}, 400


bp.add_url_rule('/colors', view_func=ColorsView.as_view('colors'))