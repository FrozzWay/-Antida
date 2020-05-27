from flask import (
Blueprint, session, request, jsonify
)

from src.database import db
from flask.views import MethodView

bp = Blueprint('colors', __name__)


class ColorsView(MethodView):
    def get(self):
        con = db.connection
        cursor = con.execute(
            'SELECT * FROM color'
        )
        colors = [dict(row) for row in cursor.fetchall()]
        return jsonify(colors), 200

    def post(self):
        user_id = session.get("user_id")
        if user_id is None:
            return '', 403

        con = db.connection
        cursor = con.execute(f'SELECT * FROM seller WHERE seller.id = {user_id}')
        if cursor.fetchone() is None:
            return '', 403

        request_json = request.json
        name = request_json.get('name')
        hex = request_json.get('hex')

        con.execute('INSERT INTO color (name, hex) VALUES (?, ?)', (name, hex))
        con.commit()

        cursor = con.execute('SELECT id FROM color WHERE color.hex = ?', (hex,))
        color_id = dict(cursor.fetchone())['id']

        response = {
            "id": color_id,
            "name": name,
            "hex": hex
        }

        return jsonify(response), 200


bp.add_url_rule('/colors', view_func=ColorsView.as_view('colors'))