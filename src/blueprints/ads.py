from flask import (
    Blueprint, request
)
from flask.views import MethodView

import src.auth as a
from src.services.sqllite import *

bp = Blueprint('ads', __name__)


# Добавление объявления
class AdsView(MethodView):
    def get(self, account_id=None):
        # Export Query
        seller_id = get_seller_id(account_id) if get_seller_id(account_id) else request.args.get('seller_id')
        if seller_id is None and account_id is not None:
            response = {
                "error": "nothing found"
            }
            return jsonify(response), 404
        tags = request.args.get('tags')
        if tags:
            tags = request.args.get('tags').split(',')
        make = request.args.get('make')
        model = request.args.get('model')
        con = db.connection
        return get_all_filters(con.cursor(), seller_id, make, model, tags)

    @a.seller_auth_required
    def post(self, user_id, seller_id, account_id=None):
        if account_id is not None and user_id != account_id:
            response = {
                "error": "not your id on route"
            }
            return jsonify(response), 403
        request_json = request.json
        con = db.connection
        cursor = con.cursor()
        car = request_json.get('car')
        add_car(cursor, car)
        car_id = cursor.lastrowid
        add_colors(cursor, car, car_id)
        add_images(cursor, car, car_id)
        add_ad(cursor, request_json, seller_id, car_id)
        ad_id = cursor.lastrowid
        add_tags(cursor, request_json, ad_id)
        con.commit()

    # Making Response
        # То, чего нет в запросе
        date = f'{int(datetime.today().timestamp())}'
        response = {
            "id": ad_id,
            "seller_id": seller_id,
            "date": datetime.utcfromtimestamp(int(date))
        }
        # Берем из запроса
        response.update(request_json)
        response['car']['colors'] = get_colors(cursor, car_id)
        return jsonify(response), 200


# Частичное изменение объявления и его просмотр
class PatchAdsView(MethodView):
    def get(self, ad_id):
        con = db.connection
        service = AdsServices(con)
        return jsonify(service.get_one_ad(ad_id)), 200

    @a.specific_seller_auth_required
    def patch(self, ad_id, user_id, seller_id, car_id):
        con = db.connection
        cursor = con.cursor()

    # Редактируем объявление (ad)
        request_json = request.json
        car = request_json.get('car')
        title = request_json.get('title')
        if title:
            update_title(cursor, ad_id, title)

    # Редактируем Tags
        if request_json.get('tags') is not None:
            delete_tags(cursor, ad_id)
            add_tags(cursor, request_json, ad_id)

    # Редактируем colors
        if car.get('colors') is not None:
            delete_colors(cursor, car_id)
            add_colors(cursor, car, car_id)

    # Редактируем images
        if car.get('images') is not None:
            delete_images(cursor, car_id)
            add_images(cursor, car, car_id)

    # Редактируем car
        car = {
            "make": car.get('make'),
            "model": car.get('model'),
            "mileage": car.get("mileage"),
            "num_owners": car.get("num_owners"),
            "reg_number": car.get("reg_number")
        }
        car_params = ','.join(f" {key} = '{val}'" for key, val in car.items() if val is not None)
        if car_params:
            update_car(cursor, car_id, car_params)

        con.commit()
        return self.get(ad_id)

    @a.specific_seller_auth_required
    def delete(self, ad_id, user_id, seller_id, car_id):
        con = db.connection
        service = AdsServices(con)
        service.delete_ad(ad_id, car_id)
        con.commit()
        return '', 200


bp.add_url_rule('/ads', view_func=AdsView.as_view('ads'))
bp.add_url_rule('/users/<int:account_id>/ads', view_func=AdsView.as_view('ads2'))

bp.add_url_rule('/ads/<int:ad_id>', view_func=PatchAdsView.as_view('patch_ads'))