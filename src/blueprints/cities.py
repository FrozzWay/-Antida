from flask import (
    Blueprint, request, jsonify
)
from flask.views import MethodView

from src.database import db

bp = Blueprint('cities', __name__)


class CitiesView(MethodView):
    def get(self):
        con = db.connection
        cursor = con.execute(
            'SELECT * FROM city'
        )
        cities = [dict(row) for row in cursor.fetchall()]
        return jsonify(cities), 200

    def post(self):
        name = request.json.get('name')
        con = db.connection
        cursor = con.cursor()
        cursor.execute(
            f'INSERT INTO city (name) VALUES (?);', (name,)
        )
        con.commit()
        response = {
            "id": cursor.lastrowid,
            "name": name
        }
        return jsonify(response), 200


bp.add_url_rule('/cities', view_func=CitiesView.as_view('city'))