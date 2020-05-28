import sqlite3


def create_db(db_name):
    with sqlite3.connect(db_name) as con:
        c = con.cursor()

        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS account(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL);
            '''
        )

        c.execute(
             '''
             CREATE TABLE IF NOT EXISTS seller(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zip_code INTEGER NOT NULL,
                street TEXT NOT NULL,
                home TEXT NOT NULL,
                phone TEXT NOT NULL,
                account_id INTEGER NOT NULL REFERENCES account(id),
                city_id INTEGER NOT NULL);
             '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS ad(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                car_id INTEGER NOT NULL REFERENCES car(id),
                seller_id INTEGER NOT NULL REFERENCES seller(id),
                posted TEXT NOT NULL
                );
             '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS car(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                num_owners INTEGER DEFAULT 1,
                reg_number TEXT NOT NULL,
                mileage INTEGER NOT NULL);
             '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS tag(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE);
             '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS AdTag(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id INTEGER NOT NULL REFERENCES tag(id),
                ad_id INTEGER NOT NULL REFERENCES ad(id));
             '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS color(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hex TEXT NOT NULL UNIQUE);
             '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS carcolor(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                color_id INTEGER NOT NULL REFERENCES color(id),
                car_id INTEGER NOT NULL REFERENCES car(id));
             '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS city(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE);
             '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS zipcode(
                zip_code INTEGER PRIMARY KEY,
                city_id INTEGER NOT NULL REFERENCES city(id));
            '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS image(
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL);
            '''
        )
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS carimage(
                id INTEGER PRIMARY KEY,
                car_id INTEGER NOT NULL REFERENCES car(id),
                image_id TEXT NOT NULL REFERENCES image(id));
            '''
        )