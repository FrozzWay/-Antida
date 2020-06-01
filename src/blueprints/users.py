from flask import (
    Blueprint, request
)
from flask.views import MethodView
from werkzeug.security import generate_password_hash

import src.auth as a
from src.services.sqllite import *

bp = Blueprint('users', __name__)


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
    create_account(cursor, user, password_hash)
    con.commit()
    if is_seller is not False:
        user['id'] = cursor.lastrowid
        create_seller(cursor, user, user['id'])
        con.commit()
        try:
            create_zipcode(cursor, user)
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
