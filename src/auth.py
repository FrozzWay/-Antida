from functools import wraps

from flask import session

from src.database import db

from src.services.ads import AdsServices


def login():
    user_id = session.get('user_id')
    if user_id is None:
        return
    with db.connection as con:
        cursor = con.execute(
            f'SELECT id FROM account WHERE account.id = {user_id}'
        )
    if cursor.fetchone() is None:
        return
    return user_id


def get_seller_id(user_id):
    connection = db.connection
    cursor = connection.cursor()
    cursor.execute(
        'SELECT id '
        'FROM seller '
        'WHERE seller.account_id = ?;',
        (user_id,)
    )
    seller_id = cursor.fetchone()
    if seller_id:
        return seller_id['id']


def auth_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = login()
        if user_id is None:
            return 'need to login', 403
        return view_func(*args, **kwargs, user_id=user_id)
    return wrapper


def seller_auth_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = login()
        if user_id is None:
            return 'need to login', 403

        seller_id = get_seller_id(user_id)
        if seller_id is None:
            return 'you have to be seller', 403

        return view_func(*args, **kwargs, user_id=user_id, seller_id=seller_id)
    return wrapper


def specific_seller_auth_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = login()
        if user_id is None:
            return 'need to login', 403

        seller_id = get_seller_id(user_id)
        if seller_id is None:
            return 'you have to be seller', 403

        service = AdsServices(db.connection)
        account_id, seller_id, car_id = service.get_ad__account_info(kwargs['ad_id'])
        # check if ad belongs to this user
        if account_id is None or account_id != user_id:
            return 'not your ad', 403

        return view_func(*args, **kwargs, user_id=user_id, seller_id=seller_id, car_id=car_id)
    return wrapper

