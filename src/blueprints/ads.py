from flask import (
    Blueprint, session, request, jsonify
)
from flask.views import MethodView
from src.database import db
from datetime import datetime

import src.auth as a
from src.services.ads import AdsServices

bp = Blueprint('ads', __name__)


# Нечитабельный hard coding этой функции
def get_all_filters(cursor, seller_id=None, make=None, model=None, tags=None):
    data = []
    ads_id_filter_by_tags = set()
    print(type(tags))
    if tags is not None:
        tags = [(record,) for record in tags]
        print(f'tupled tags = {tags}')
        for tag in tags:  # Поиск tags с заданным именем в бд
            cursor.execute(
                f'SELECT id FROM tag WHERE name = ?;', tag
            )
            data.append(cursor.fetchone())
        print(f'data - {data}')
        if data:
            tags_id = [(row['id'],) for row in data]  # [(id1,),(id2,)...]
            for tag_id in tags_id:  # Поиск объявлений с заданными тегами в бд
                cursor.execute(
                    f'SELECT ad_id FROM adtag WHERE tag_id = ?', tag_id
                )
                data = cursor.fetchall()
                if data:
                    for ad_id in data:
                        t = ad_id['ad_id']
                        ads_id_filter_by_tags.add(f'= {t}')
    if len(ads_id_filter_by_tags) == 0:
        ads_id_filter_by_tags = ['IS NOT NULL']
    ads_id = []
    query = {
        "seller_id": seller_id,
        "make": make,
        "model": model
    }

    query_params = 'AND '.join(f"{key} = '{val}' " for key, val in query.items() if val is not None)
    if query_params:
        query_params = 'AND ' + query_params

    for ad_id in ads_id_filter_by_tags:
        print(f'WHERE ad.id {ad_id} {query_params}')
        cursor.execute(
            f'SELECT ad.id '
            f'FROM ad '
            f'JOIN car ON car.id = ad.car_id '
            f'WHERE ad.id {ad_id} {query_params}'
        )
        data = cursor.fetchall()
        if data:
            for record in data:
                ads_id.append(record['id'])

    con = db.connection
    service = AdsServices(con)
    response = []
    if not ads_id:
        return 'nothing found', 404
    for ad_id in ads_id:
        response.append(service.get_one_ad(ad_id))
    return jsonify(response), 200


def add_tags(cursor, request_json, ad_id):
    tags = [(tag,) for tag in request_json.get('tags')]  # list of tuples [(tag,), (tag2,)...]
    tags_id_list = []  # list of tags-id for this ad [(id,), (id2,)...]
    # try чтобы не ловить except на unique
    for tag in tags:
        try:
            cursor.execute(
                'INSERT INTO tag (name) '
                'VALUES (?);',
                tag
            )
        except:
            pass
    for tag in tags:
        cursor.execute(
            'SELECT id FROM tag WHERE tag.name = ?;',
            tag
        )
        tag_id = cursor.fetchone()['id']
        tags_id_list.append((tag_id,))
    cursor.executemany(
        f'''
                INSERT INTO AdTag (ad_id, tag_id)
                VALUES ({ad_id}, ?);
                ''',
        tags_id_list
    )


def add_colors(cursor, car, car_id):
    colors = [(color,) for color in car.get('colors')]
    cursor.executemany(
        f'''
                INSERT INTO carcolor (color_id, car_id)
                VALUES (?, {car_id});
                ''',
        colors
    )


def add_images(cursor, car, car_id):
    images = car.get('images')  # list of images from request [{title: smth, url: smth2}, ...]
    data = []  # list of tuples [(smth, smth2), ...]

    # Заполнение <variable> data
    for image in images:
        title = image.get('title')
        url = image.get('url')
        data.append((title, url))

    images_id_list = []  # list of images-id for this car [(id,), (id2,)...]

    # Добавление <sql> записей в image
    # Не использую executemany, потому что нужны id каждой новой записи в таблице image
    for image in data:
        cursor.execute(
            'INSERT INTO image (title, url) '
            'VALUES (?, ?);',
            image
        )
        images_id_list.append((cursor.lastrowid,))

    cursor.executemany(
        'INSERT INTO carimage (car_id, image_id) '
        f'VALUES ({car_id}, ?);', images_id_list
    )


def add_car(cursor, car):
    cursor.execute(
        'INSERT INTO car (make, model, mileage, reg_number, num_owners) '
        'VALUES (?, ?, ?, ?, ?);',
        (car['make'], car['model'], car['mileage'], car['reg_number'], car.get('num_owners'))
    )


def add_ad(cursor, request_json, seller_id, car_id):
    title = request_json.get('title')
    date = f'{int(datetime.today().timestamp())}'
    cursor.execute(
        'INSERT INTO ad (title, car_id, seller_id, date) '
        'VALUES (?, ?, ?, ?);',
        (title, car_id, seller_id, date)
    )


def delete_tags(cursor, ad_id):
    cursor.execute(
        f'DELETE FROM AdTag WHERE ad_id = {ad_id}'
    )


def delete_colors(cursor, car_id):
    cursor.execute(
        f'DELETE FROM carcolor WHERE car_id = {car_id}'
    )


def delete_images(cursor, car_id):
    cursor.execute(
        f'SELECT id from carimage WHERE car_id = {car_id}'
    )
    images_id_list = [tuple(dict(row).values()) for row in cursor.fetchall()]
    cursor.executemany(
        f'DELETE FROM image WHERE id = ?;', images_id_list
    )
    cursor.execute(
        f'DELETE FROM carimage WHERE car_id = {car_id}'
    )


def update_title(cursor, ad_id, title):
    cursor.execute(f'UPDATE ad SET title = "{title}" WHERE ad.id = {ad_id}')


def update_car(cursor, car_id, car_params):
    cursor.execute(f'UPDATE car SET{car_params} WHERE id = {car_id};')


# Добавление объявления
class AdsView(MethodView):
    def get(self, account_id=None):
        # Export Query
        seller_id = account_id if account_id else request.args.get('seller_id')
        tags = request.args.get('tags').split(',')
        print(tags)
        make = request.args.get('make')
        model = request.args.get('model')
        con = db.connection
        return get_all_filters(con.cursor(), seller_id, make, model, tags)

    @a.seller_auth_required
    def post(self, user_id, seller_id, account_id=None):
        if account_id is not None and user_id != account_id:
            return 'not your id on route', 403
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
        # Берем из Бд
        cursor.execute(
            'SELECT color.id, color.name, color.hex '
            'FROM color '
            'JOIN carcolor ON carcolor.color_id = color.id '
            'WHERE carcolor.car_id = ?;',
            (car_id,)
        )
        colors = [dict(row) for row in cursor.fetchall()]
        response['car']['colors'] = colors
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