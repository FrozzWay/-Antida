from datetime import datetime


def get_ad(cursor, ad_id):
    cursor.execute(
        f'SELECT * FROM ad WHERE ad.id = {ad_id};'
    )
    fetched = cursor.fetchone()
    if fetched is None:
        return None
    response = dict(fetched)
    response["date"] = datetime.utcfromtimestamp(int(response['date']))
    return response


def get_tags(cursor, ad_id):
    cursor.execute(
        'SELECT tag.name FROM tag '
        'JOIN adtag ON adtag.tag_id = tag.id '
        'JOIN ad ON ad.id = adtag.ad_id '
        'WHERE ad.id = ?;', (ad_id,)
    )
    return [dict(row)['name'] for row in cursor.fetchall()]


def get_car(cursor, car_id):
    cursor.execute(
        f'SELECT * FROM car WHERE car.id = {car_id};'
    )
    response = dict(cursor.fetchone())
    del (response['id'])
    return response


def get_colors(cursor, car_id):
    cursor.execute(
        'SELECT color.id, color.name, color.hex '
        'FROM color '
        'JOIN carcolor ON carcolor.color_id = color.id '
        'JOIN car ON car.id = carcolor.car_id '
        'WHERE car.id = ?;', (car_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


def get_images(cursor, car_id):
    cursor.execute(
        'SELECT image.title, image.url '
        'FROM image '
        'JOIN carimage ON carimage.image_id = image.id '
        'JOIN car on car.id = carimage.car_id '
        'WHERE car.id = ?;', (car_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


class AdsServices:
    def __init__(self, connection):
        self.con = connection

    def get_ad__account_info(self, ad_id):
        cursor = self.con.cursor()
        cursor.execute(
            'SELECT seller_id, car_id, account_id '
            'FROM ad '
            'JOIN seller ON seller.id = ad.seller_id '
            'JOIN account ON account.id = seller.account_id '
            'WHERE ad.id = ?',
            (ad_id,)
        )
        info = dict(cursor.fetchone())
        account_id = info.get('account_id')
        seller_id = info.get('seller_id')
        car_id = info.get('car_id')
        return account_id, seller_id, car_id

    def delete_ad(self, ad_id, car_id):
        cursor = self.con.cursor()
        cursor.execute(
            f'DELETE FROM ad WHERE id = {ad_id};'
        )
        cursor.execute(
            f'DELETE FROM car WHERE id = {car_id};'
        )
        cursor.execute(
            f'DELETE FROM carcolor WHERE car_id = {car_id};'
        )
        cursor.execute(
            f'DELETE FROM adtag WHERE ad_id = {ad_id}'
        )
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

    def get_one_ad(self, ad_id):
        cursor = self.con.cursor()
        response = get_ad(cursor, ad_id)
        car_id = response['car_id']
        response['tags'] = get_tags(cursor, ad_id)
        response['car'] = get_car(cursor, car_id)
        response['car']['colors'] = get_colors(cursor, car_id)
        response['car']['images'] = get_images(cursor, car_id)

        del (response['car_id'])
        return response
