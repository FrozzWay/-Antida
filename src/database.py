import sqlite3

from src.database_create import create_db

db_name = 'database.db'


class Sqlite3Db:
    def __init__(self):
        self._connection = None
        self._app = None
        create_db(db_name)

    def init_app(self, app):
        self._app = app
        self._app.teardown_appcontext(self.close_db)

    def close_db(self, exception):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _connect(self):
        self._connection = sqlite3.connect(
            db_name,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self._connection.row_factory = sqlite3.Row

    @property
    def connection(self):
        self._connect()
        return self._connection


db = Sqlite3Db()
