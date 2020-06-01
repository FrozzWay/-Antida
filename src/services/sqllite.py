from datetime import datetime
from flask import jsonify
from src.database import db
from src.services.ads import AdsServices


# Нечитабельный hard coding этой функции
def get_all_filters(cursor, seller_id=None, make=None, model=None, tags=None):
    data = []
    ads_id_filter_by_tags = set()
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
            tags_id = [(row['id'],) for row in data if row is not None]  # [(id1,),(id2,)...]
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


def get_colors(cursor, car_id):
    cursor.execute(
        'SELECT color.id, color.name, color.hex '
        'FROM color '
        'JOIN carcolor ON carcolor.color_id = color.id '
        'WHERE carcolor.car_id = ?;',
        (car_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


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


def create_account(cursor, user, password_hash):
    cursor.execute(
        'INSERT INTO account (email, password, first_name, last_name) '
        'VALUES (?,?,?,?); ',
        (user['email'], password_hash, user['first_name'], user['last_name'])
    )


def create_seller(cursor, seller, user_id):
    cursor.execute(
        'INSERT INTO seller (zip_code, street, home, phone, city_id, account_id) '
        'VALUES (?,?,?,?,?,?);',
        (seller['zip_code'], seller['street'], seller['home'], seller['phone'], seller['city_id'], user_id)
    )


def create_zipcode(cursor, user):
    cursor.execute(
        'INSERT INTO zipcode (zip_code, city_id) '
        'VALUES (?,?);',
        (user['zip_code'], user['city_id'])
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