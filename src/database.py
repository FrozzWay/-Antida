import sqlite3


class Sqlite3Db:
    def __init__(self):
        self._connection = None
        self._app = None

    def init_app(self, app):
        self._app = app
        self._app.teardown_appcontext(self.close_db)

    def close_db(self, exception):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _connect(self):
        self._connection = sqlite3.connect(
            'example_2.db',
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self._connection.row_factory = sqlite3.Row

    @property
    def connection(self):
        self._connect()
        return self._connection


db = Sqlite3Db()
