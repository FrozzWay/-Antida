from flask import (
    Blueprint, session, request, jsonify
)
from flask.views import MethodView
from src.database import db
from datetime import datetime

bp = Blueprint('ads', __name__)


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


# Добавление объявления
class AdsView(MethodView):
    def post(self, id=None):
        # check for login
        user_id = session.get('user_id')
        if user_id is None:
            return 'need to login', 403
        if id is not None and id != user_id:
            return 'not your id on route', 403
    # check for seller
        con = db.connection
        cursor = con.execute(
            'SELECT id '
            'FROM seller '
            'WHERE seller.account_id = ?;',
            (user_id,)
        )
        seller_id = cursor.fetchone()['id']

        if seller_id is None:
            return 'you have to be seller', 403

        request_json = request.json
        title = request_json.get('title')
        posted = f'{int(datetime.today().timestamp())}'

    # Add car
        car = request_json.get('car')
        cursor.execute(
            'INSERT INTO car (make, model, mileage, reg_number, num_owners) '
            'VALUES (?, ?, ?, ?, ?);',
            (car['make'], car['model'], car['mileage'], car['reg_number'], car.get('num_owners'))
        )
        car_id = cursor.lastrowid

    # Add ad
        cursor.execute(
            'INSERT INTO ad (title, car_id, seller_id, posted) '
            'VALUES (?, ?, ?, ?);',
            (title, car_id, seller_id, posted)
        )
        ad_id = cursor.lastrowid

    # Add colors
        add_colors(cursor, car, car_id)

    # Add images
        add_images(cursor, car, car_id)

    # Add Tags
        add_tags(cursor, request_json, ad_id)
        con.commit()

    # Making Response
        # То, чего нет в запросе
        response = {
            "id": ad_id,
            "seller_id": seller_id,
            "posted": datetime.utcfromtimestamp(int(posted))
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

        # from Ad
        cursor = con.cursor()
        cursor.execute(
            f'SELECT id, title, posted, car_id, seller_id FROM ad WHERE ad.id = {ad_id};'
        )
        response = dict(cursor.fetchone())
        car_id = response['car_id']
        del(response['car_id'])
        response["posted"] = datetime.utcfromtimestamp(int(response['posted']))

        # from tag
        cursor.execute(
            'SELECT tag.name FROM tag '
                'JOIN adtag ON adtag.tag_id = tag.id '
                'JOIN ad ON ad.id = adtag.ad_id '
            'WHERE ad.id = ?;', (ad_id,)
        )
        response['tags'] = [dict(row)['name'] for row in cursor.fetchall()]

        # from car
        cursor.execute(
            f'SELECT * FROM car WHERE car.id = {car_id};'
        )
        response['car'] = dict(cursor.fetchone())
        del(response['car']['id'])

        # from colors
        cursor.execute(
            'SELECT color.id, color.name, color.hex '
            'FROM color '
                'JOIN carcolor ON carcolor.color_id = color.id '
                'JOIN car ON car.id = carcolor.car_id '
            'WHERE car.id = ?;', (car_id,)
        )
        response['car']['colors'] = [dict(row) for row in cursor.fetchall()]

        # from images
        cursor.execute(
            'SELECT image.title, image.url '
            'FROM image '
                'JOIN carimage ON carimage.image_id = image.id '
                'JOIN car on car.id = carimage.car_id '
            'WHERE car.id = ?;', (car_id,)
        )
        response['car']['images'] = [dict(row) for row in cursor.fetchall()]
        return jsonify(response), 200

    def patch(self, ad_id=None):
        # check for login
        user_id = session.get('user_id')
        if user_id is None:
            return 'need to login', 403

        con = db.connection
        cursor = con.cursor()

        # check for seller
        cursor.execute(
            'SELECT id '
            'FROM seller '
            'WHERE seller.account_id = ?;',
            (user_id,)
        )
        seller_id = cursor.fetchone()['id']

        if seller_id is None:
            return 'you have to be seller', 403

        # check if ad belongs to this seller
        cursor.execute(
            'SELECT seller_id, car_id, account_id '
            'FROM ad '
                'JOIN seller ON seller.id = ad.seller_id '
                'JOIN account ON account.id = seller.account_id '
            'WHERE ad.id = ?',
            (ad_id,)
        )
        res = dict(cursor.fetchone())
        seller_id = res.get('seller_id')
        car_id = res.get('car_id')
        account_id = res.get('account_id')

        if account_id is None or account_id != user_id:
            return 'not your ad', 403

    # Редактируем объявление (ad)
        request_json = request.json
        car = request_json.get('car')
        title = request_json.get('title')
        if title:
            cursor.execute(
                f'UPDATE ad SET title = "{title}" WHERE ad.id = {ad_id}'
            )

    # Редактируем Tags
        if request_json.get('tags') is not None:
            cursor.execute(
                f'DELETE FROM AdTag WHERE ad_id = {ad_id}'
            )
            add_tags(cursor, request_json, ad_id)

    # Редактируем colors
        if car.get('colors') is not None:
            cursor.execute(
                f'DELETE FROM carcolor WHERE car_id = {car_id}'
            )
            add_colors(cursor, car, car_id)

    # Редактируем images
        if car.get('images') is not None:
            cursor.execute(
                f'DELETE FROM carimage WHERE car_id = {car_id}'
            )
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
            cursor.execute(f'UPDATE car SET{car_params} WHERE id = {car_id};')
        con.commit()
        return self.get(ad_id)


bp.add_url_rule('/ads', view_func=AdsView.as_view('ads'))
bp.add_url_rule('/users/<int:ad_id>/ads', view_func=AdsView.as_view('ads2'))

bp.add_url_rule('/ads/<int:ad_id>', view_func=PatchAdsView.as_view('patch_ads'))