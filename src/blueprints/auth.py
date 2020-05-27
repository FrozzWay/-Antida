from flask import (
    request,
    Blueprint,
    session
)
from werkzeug.security import check_password_hash, generate_password_hash
from src.database import db

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login():
    request_json = request.json
    email = request_json.get('email')
    password = request_json.get('password')

    con = db.connection
    cursor = con.execute(
        'SELECT * '
        'FROM account '
        'WHERE account.email = ?',
        (email,)
    )
    user = cursor.fetchone()

    if not check_password_hash(user['password'], password):
        print(generate_password_hash(password))
        print(user['password'])
        return '', 403

    session['user_id'] = user['id']
    return '', 200


@bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return '', 200

