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
            return 'need login first', 403

        con = db.connection
        cursor = con.execute(f'SELECT * FROM seller WHERE seller.account_id = {user_id}')
        if cursor.fetchone() is None:
            return 'you are not a seller', 403

        request_json = request.json
        name = request_json.get('name')
        hex = request_json.get('hex')

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


bp.add_url_rule('/colors', view_func=ColorsView.as_view('colors'))