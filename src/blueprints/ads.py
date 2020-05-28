from flask import (
    Blueprint, session, request, jsonify
)
from flask.views import MethodView
from src.database import db
from datetime import datetime

bp = Blueprint('ads', __name__)


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
        colors = [(color,) for color in car.get('colors')]
        cursor.executemany(
            f'''
            INSERT INTO carcolor (color_id, car_id)
            VALUES (?, {car_id});
            ''',
            colors
        )

    # Add images
        images = car.get('images')  # list of images from request [{title: smth, url: smth2}, ...]
        data = [] # list of tuples [(smth, smth2), ...]

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

        # Добавление <sql> записей в carimage
        cursor.executemany(
            f'''
            INSERT INTO carimage (car_id, image_id)
            VALUES ({car_id}, ?);
            ''',
            images_id_list
        )

    # Add Tags
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
            except: pass
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


bp.add_url_rule('/ads', view_func=AdsView.as_view('ads'))
bp.add_url_rule('/users/<int:id>/ads', view_func=AdsView.as_view('ads2'))