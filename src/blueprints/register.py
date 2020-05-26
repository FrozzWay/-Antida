import sqlite3
from flask import (
    Blueprint,
    request
)
from src.database import db
from werkzeug.security import generate_password_hash

bp = Blueprint('auth', __name__)


@bp.route('/users', methods=['POST'])
def register():
    request_json = request.json
    
    email = request_json.get('email')
    password = request_json.get('password')
    first_name = request_json.get('first_name')
    last_name = request_json.get('password')
    is_seller = request_json.get('is_seller')
    phone = request_json.get('phone')
    zip_code = request_json.get('zip_code')
    city_id = request_json.get('city_id')
    street = request_json.get('street')
    home = request_json.get('home')

    password_hash = generate_password_hash(password)

    con = db.connection
    cursor = con.cursor()
    cursor.execute(
        'INSERT INTO account (email, password, first_name, last_name) '
        'VALUES (?,?,?,?); ',
        (email, password_hash, first_name, last_name)
    )
    con.commit()
    if is_seller is not None:
        cursor.execute(
            'SELECT id '
            'FROM account '
            'WHERE account.email = ?; ',
            (email,)
        )
        account_id = cursor.fetchone()['id']
        print(account_id)
        cursor.execute(
            'INSERT INTO seller (zip_code, street, home, phone, city_id, account_id) '
            'VALUES (?,?,?,?,?,?);',
            (zip_code, street, home, phone, city_id, account_id)
        )
        con.commit()
    return '', 200
