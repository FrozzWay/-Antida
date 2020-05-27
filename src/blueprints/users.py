import sqlite3
from flask import (
    Blueprint,
    request,
    jsonify,
    session
)
from flask.views import MethodView
from src.database import db
from werkzeug.security import generate_password_hash

bp = Blueprint('users', __name__)


@bp.route('/', methods=["POST"])
def register():
    request_json = request.json

    is_seller = request_json.get('is_seller')
    is_seller = True if is_seller else False

    user= {
        "email": request_json.get('email'),
        "password": request_json.get('password'),
        "first_name": request_json.get('first_name'),
        "last_name": request_json.get('password'),
        "is_seller": is_seller,
        "phone": request_json.get('phone'),
        "zip_code": request_json.get('zip_code'),
        "city_id": request_json.get('city_id'),
        "street": request_json.get('street'),
        "home": request_json.get('home'),
    }

    password_hash = generate_password_hash(user['password'])
    print(user['password'])
    print(password_hash)
    con = db.connection
    cursor = con.cursor()
    cursor.execute(
        'INSERT INTO account (email, password, first_name, last_name) '
        'VALUES (?,?,?,?); ',
        (user['email'], password_hash, user['first_name'], user['last_name'])
    )
    con.commit()
    if is_seller is not False:
        cursor.execute(
            'SELECT id '
            'FROM account '
            'WHERE account.email = ?; ',
            (user['email'],)
        )
        account_id = cursor.fetchone()['id']
        user['id'] = account_id
        print(account_id)
        cursor.execute(
            'INSERT INTO seller (zip_code, street, home, phone, city_id, account_id) '
            'VALUES (?,?,?,?,?,?);',
            (user['zip_code'], user['street'], user['home'], user['phone'], user['city_id'], account_id)
        )
        con.commit()
    return jsonify(user), 200


class UsersView(MethodView):
    def get(self, id):
        user_id = session.get('user_id')
        if user_id is None:
            return '', 403
        con = db.connection
        cursor = con.execute(
            'SELECT * '
            'FROM account '
            'WHERE account.id = ?',
            (id,)
        )
        account = dict(cursor.fetchone())
        account['is_seller'] = False
        del(account['password'])
        cursor.execute(
            'SELECT zip_code, street, phone, home '
            'FROM seller '
            'WHERE seller.account_id= ?',
            (account['id'],)
        )
        seller = cursor.fetchone()
        if seller is None:
            return jsonify(account), 200
        seller = dict(seller)
        account.update(seller)
        account['is_seller'] = True
        return jsonify(account), 200



bp.add_url_rule('/<int:id>', view_func=UsersView.as_view('users'))
