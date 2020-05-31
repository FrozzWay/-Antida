from flask import (
    Blueprint, request, jsonify, session
)
from flask.views import MethodView
from src.database import db
from werkzeug.security import generate_password_hash

import src.auth as a
from src.services.ads import AdsServices


bp = Blueprint('users', __name__)


def get_seller_id(user_id):
    connection = db.connection
    cursor = connection.cursor()
    cursor.execute(
        'SELECT id '
        'FROM seller '
        'WHERE seller.account_id = ?;',
        (user_id,)
    )
    data = cursor.fetchone()
    seller_id = data['id'] if data else None

    return seller_id


def delete_seller(cursor, user_id):
    cursor.execute(
        f'DELETE FROM seller WHERE account_id = {user_id};'
    )


def create_seller(cursor, seller, user_id):
    cursor.execute(
        'INSERT INTO seller (zip_code, street, home, phone, city_id, account_id) '
        'VALUES (?,?,?,?,?,?);',
        (seller['zip_code'], seller['street'], seller['home'], seller['phone'], seller['city_id'], user_id)
    )


def get_ad_id__car_id(cursor, seller_id):
    cursor.execute(
        f'SELECT id, car_id FROM ad WHERE seller_id = {seller_id}'
    )
    info = cursor.fetchall()
    ad_id_list = [(dict(row)['id'], dict(row)['car_id']) for row in info if row is not None]
    return ad_id_list


def get_account(cursor, ac_id):
    cursor.execute(
        'SELECT * '
        'FROM account '
        'WHERE account.id = ?',
        (ac_id,)
    )
    fetched = cursor.fetchone()
    account = dict(fetched) if fetched else None
    return account


def get_seller(cursor, user_id):
    cursor.execute(
        'SELECT zip_code, street, phone, home '
        'FROM seller '
        'WHERE seller.account_id= ?',
        (user_id,)
    )
    seller = cursor.fetchone()
    return seller


def update_seller(cursor, seller_params, user_id):
    cursor.execute(f'UPDATE seller SET{seller_params} WHERE account_id = {user_id};')


def update_account(cursor, account_params, user_id):
    cursor.execute(f'UPDATE account SET{account_params} WHERE id = {user_id};')


# Регистрация аккаунта
@bp.route('', methods=["POST"])
def register():
    request_json = request.json

    is_seller = request_json.get('is_seller')
    is_seller = True if is_seller else False

    user = {
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

    con = db.connection
    cursor = con.cursor()
    cursor.execute(
        'INSERT INTO account (email, password, first_name, last_name) '
        'VALUES (?,?,?,?); ',
        (user['email'], password_hash, user['first_name'], user['last_name'])
    )
    con.commit()
    if is_seller is not False:
        user['id'] = cursor.lastrowid
        cursor.execute(
            'INSERT INTO seller (zip_code, street, home, phone, city_id, account_id) '
            'VALUES (?,?,?,?,?,?);',
            (user['zip_code'], user['street'], user['home'], user['phone'], user['city_id'], user['id'])
        )
        con.commit()
        try:
            cursor.execute(
                'INSERT INTO zipcode (zip_code, city_id) '
                'VALUES (?,?);',
                (user['zip_code'], user['city_id'])
            )
            con.commit()
        except:
            pass
    return jsonify(user), 200


# Получение данных об аккаунте и их изменение
class UsersView(MethodView):
    @a.auth_required
    def get(self, ac_id, user_id):
        con = db.connection
        cursor = con.cursor()

        account = get_account(cursor, ac_id)

        if account is None:
            return 'no account', 404

        account['is_seller'] = False
        del(account['password'])

        seller = get_seller(cursor, user_id)

        if seller is None:
            return jsonify(account), 200

        seller = dict(seller)
        account.update(seller)
        account['is_seller'] = True
        return jsonify(account), 200

    @a.auth_required
    def patch(self, ac_id, user_id):
        if ac_id != user_id:
            return "not your id in route", 403

        request_json = request.json
        account = {
            "first_name": request_json.get('first_name'),
            "last_name": request_json.get('password'),
        }
        is_seller = request_json.get('is_seller')
        seller = {
            "phone": request_json.get('phone'),
            "zip_code": request_json.get('zip_code'),
            "city_id": request_json.get('city_id'),
            "street": request_json.get('street'),
            "home": request_json.get('home'),
        }

        account_params = ','.join(f" {key} = '{val}'" for key, val in account.items() if val is not None)
        seller_params = ','.join(f" {key} = '{val}'" for key, val in seller.items() if val is not None)

        con = db.connection
        cursor = con.cursor()
        seller_id = get_seller_id(user_id)
        if is_seller is False:
            delete_seller(cursor, user_id)
            ad_id_list = get_ad_id__car_id(cursor, seller_id) # [(ad_id, car_id), ... ]
            if ad_id_list:
                service = AdsServices(con)
                for record in ad_id_list:
                    service.delete_ad(record[0], record[1])
        if seller_id and seller_params and is_seller:
            update_seller(cursor, seller_params, user_id)
        if seller_id is None and seller_params and is_seller:
            create_seller(cursor, seller, user_id)
        if account_params:
            update_account(cursor, account_params, user_id)

        con.commit()
        return self.get(user_id)


bp.add_url_rule('/<int:ac_id>', view_func=UsersView.as_view('users'))
