import sqlite3
from flask import (
    Blueprint,
    request,
    jsonify
)
from src.database import db
from werkzeug.security import generate_password_hash

bp = Blueprint('register', __name__)


@bp.route('/users', methods=['POST'])
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
        print(account_id)
        cursor.execute(
            'INSERT INTO seller (zip_code, street, home, phone, city_id, account_id) '
            'VALUES (?,?,?,?,?,?);',
            (user['zip_code'], user['street'], user['home'], user['phone'], user['city_id'], account_id)
        )
        con.commit()
    return jsonify(user), 200
