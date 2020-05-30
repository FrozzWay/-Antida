import sqlite3
from datetime import datetime

with sqlite3.connect('database.db') as con:
    con.row_factory = sqlite3.Row
    make = 'Mercedes'
    model = None
    tags = None
    seller_id = None
    cursor = con.cursor()
    data = []
    ads_id = set()
    if tags is not None:
        tags = [(record,) for record in tags]
        for tag in tags:  # Поиск tags с заданным именем в бд
            cursor.execute(
                f'SELECT id FROM tag WHERE name = ?;', tag
            )
            data.append(cursor.fetchone())
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
                        ads_id.add(f'= {t}')
    if len(ads_id) == 0:
        ads_id = ['IS NOT NULL']
    print(ads_id)
    response = []
    query = {
        "seller_id": seller_id,
        "make": make,
        "model": model
    }
    query_params = 'AND '.join(f"{key} = '{val}' " for key, val in query.items() if val is not None)
    if query_params:
        query_params = 'AND ' + query_params
    print(query_params)

    for ad_id in ads_id:
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
                response.append(record['id'])
    print(response)


























