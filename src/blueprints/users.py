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


# Регистрация аккаунта
@bp.route('/', methods=["POST"])
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
        cursor.execute(
            'INSERT INTO zipcode (zip_code, city_id) '
            'VALUES (?,?);',
            (user['zip_code'], user['city_id'])
        )
        con.commit()
    return jsonify(user), 200


# Получение данных об аккаунте и их изменение
class UsersView(MethodView):
    def get(self, id):
        user_id = session.get('user_id')

        if user_id is None:
            return 'need to login', 403

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

    def patch(self, id):
        user_id = session.get('user_id')
        if id != user_id:
            return 'not your id in route', 403

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

        if is_seller is False:
            cursor.execute(
                f'DELETE FROM seller WHERE account_id = {id};'
            )

        if is_seller and seller_params:
            cursor.execute(f'UPDATE seller SET{seller_params} WHERE account_id = {id};')
        if account_params:
            cursor.execute(f'UPDATE account SET{account_params} WHERE id = {id};')

        con.commit()
        return self.get(id)


bp.add_url_rule('/<int:id>', view_func=UsersView.as_view('users'))
