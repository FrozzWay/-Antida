import sqlite3

with sqlite3.connect('database.db') as con:
    con.execute("UPDATE seller SET phone = '+7000000000', street = 'Пуш000000000на' WHERE account_id = 3;")


# params = ','.join(f'{key} = ?' for key in request)
# query = f'UPDATE user SET {params} WHERE id = ?'
# con.execute(query, (*request.values(), user_id))