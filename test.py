import sqlite3
from datetime import datetime

# with sqlite3.connect('database.db') as con:
#     con.execute("UPDATE seller SET phone = '+7000000000', street = 'Пуш000000000на' WHERE account_id = 3;")

car = {
    "make": "fff",
    "model": "afaf"
}
car = {
    "make": car.get('make'),
    "model": car.get('model'),
    "mileage": car.get("mileage")
}
print(car)
# params = ','.join(f'{key} = ?' for key in request)
# query = f'UPDATE user SET {params} WHERE id = ?'
# con.execute(query, (*request.values(), user_id))
