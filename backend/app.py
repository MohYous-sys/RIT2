
import os
import secrets
from datetime import timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from .database import get_db_connection, init_databases
except ImportError:
    from database import get_db_connection, init_databases


def get_secret_key():
    configured_key = os.environ.get("FLASK_SECRET_KEY")
    if configured_key:
        return configured_key

    if os.environ.get("APP_ENV", "").lower() == "production":
        raise RuntimeError("FLASK_SECRET_KEY must be set in production")

    secret_path = Path(__file__).with_name(".flask_secret_key")
    try:
        descriptor = os.open(secret_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        key = secret_path.read_text(encoding="utf-8").strip()
        if not key:
            raise RuntimeError("FLASK_SECRET_KEY or a non-empty backend/.flask_secret_key is required")
        return key

    key = secrets.token_hex(32)
    with os.fdopen(descriptor, "w", encoding="utf-8") as secret_file:
        secret_file.write(key)
    return key


app = Flask(__name__)
app.config["SECRET_KEY"] = get_secret_key()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
is_production = os.environ.get("APP_ENV", "").lower() == "production"
app.config["SESSION_COOKIE_SECURE"] = is_production or os.environ.get(
    "SESSION_COOKIE_SECURE", "false"
).lower() in {"1", "true", "yes"}
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
app.config["DEBUG"] = not is_production and os.environ.get("FLASK_DEBUG", "").lower() in {
    "1", "true", "yes"
}
init_databases()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        account_id = session.get("account_id")
        if not isinstance(account_id, int):
            return jsonify({"error": "Login required"}), 401

        connection = get_db_connection()
        account = connection.execute(
            "SELECT id FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        connection.close()
        if not account:
            session.clear()
            return jsonify({"error": "Login required"}), 401
        return view(*args, **kwargs)

    return wrapped_view

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    name = data.get('name')
    password = data.get('password')

    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': 'Valid name required'}), 400

    if not isinstance(password, str) or not password.strip():
        return jsonify({'error': 'Valid password required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT id, password FROM accounts WHERE name = ?''', (name.strip(),))
    account = cursor.fetchone()
    conn.close()

    if not account:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not check_password_hash(account['password'], password.strip()):
        return jsonify({'error': 'Invalid credentials'}), 401

    session.clear()
    session['account_id'] = account['id']
    session.permanent = True

    return jsonify({'message': 'Login successful', 'account_id': account['id']}), 200


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200


@app.route('/session', methods=['GET'])
def get_session():
    account_id = session.get('account_id')
    if not isinstance(account_id, int):
        return jsonify({'authenticated': False}), 200

    connection = get_db_connection()
    account = connection.execute(
        'SELECT id FROM accounts WHERE id = ?', (account_id,)
    ).fetchone()
    connection.close()
    if not account:
        session.clear()
        return jsonify({'authenticated': False}), 200
    return jsonify({'authenticated': True, 'account_id': account_id}), 200

@app.route('/')
def home():
    return "Warehouse Management System"

@app.route('/accounts', methods=['GET'])
@login_required
def get_accounts():
    conn = get_db_connection()
    accounts = conn.execute('SELECT id, name FROM accounts').fetchall()
    conn.close()

    return jsonify([dict(account) for account in accounts])

@app.route('/accounts', methods=['POST'])
def add_account():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    name = data.get('name')
    password = data.get('password')
    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': 'Valid name required'}), 400

    if not isinstance(password, str) or not password.strip():
        return jsonify({'error': 'Valid password required'}), 400

    

    hashed_password = generate_password_hash(password.strip(), method='pbkdf2:sha256')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO accounts (name, password) VALUES (?, ?)''', (name.strip(), hashed_password))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Account created successfully', 'account_id': new_id}), 201



@app.route('/accounts/<int:account_id>', methods=['PUT'])
@login_required
def update_account(account_id):
    if session['account_id'] != account_id:
        return jsonify({'error': 'You can only update your own account'}), 403

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    name = data.get('name')
    password = data.get('password')

    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': 'Valid name required'}), 400

    if not isinstance(password, str) or not password.strip():
        return jsonify({'error': 'Valid password required'}), 400

    hashed_password = generate_password_hash(password.strip(), method='pbkdf2:sha256')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE accounts SET name = ?, password = ? WHERE id = ?''', (name.strip(), hashed_password, account_id))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()

    if updated_rows == 0:
        return jsonify({'error': 'Account not found'}), 404

    return jsonify({'message': 'Account updated successfully', 'account_id': account_id}), 200

@app.route('/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    if session['account_id'] != account_id:
        return jsonify({'error': 'You can only delete your own account'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM accounts WHERE id = ?''', (account_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()

    if deleted_rows == 0:
        return jsonify({'error': 'Account not found'}), 404

    session.clear()
    return jsonify({'message': 'Account deleted successfully', 'account_id': account_id}), 200

@app.route('/warehouse', methods=['GET'])
@login_required
def get_warehouse():
    conn = get_db_connection('warehouse.db')
    
    items = conn.execute('SELECT warehouse_id, item_name, quantity FROM warehouse_inventory').fetchall()
    conn.close()

    return jsonify([dict(item) for item in items])

@app.route('/places', methods=['GET'])
@login_required
def get_places():
    conn = get_db_connection('places.db')
    
    places = conn.execute('SELECT place_id, value_per_item FROM places').fetchall()
    conn.close()

    return jsonify([dict(place) for place in places])

@app.route('/places', methods=['POST'])
@login_required
def add_place():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    value_per_item = data.get('value_per_item')

    if type(value_per_item) not in (int, float) or value_per_item < 0:
        return jsonify({'error': 'Valid value per item required'}), 400

    conn = get_db_connection('places.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO places (value_per_item) VALUES (?)''', (value_per_item,))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Place added successfully', 'place_id': new_id}), 201

@app.route('/places/<int:place_id>', methods=['PUT'])
@login_required
def update_place(place_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    value_per_item = data.get('value_per_item')

    if type(value_per_item) not in (int, float) or value_per_item < 0:
        return jsonify({'error': 'Valid value per item required'}), 400

    conn = get_db_connection('places.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE places SET value_per_item = ? WHERE place_id = ?''', (value_per_item, place_id))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()

    if updated_rows == 0:
        return jsonify({'error': 'Place not found'}), 404

    return jsonify({'message': 'Place updated successfully'})

@app.route('/places/<int:place_id>', methods=['DELETE'])
@login_required
def delete_place(place_id):
    conn = get_db_connection('places.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM places WHERE place_id = ?''', (place_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()

    if deleted_rows == 0:
        return jsonify({'error': 'Place not found'}), 404

    return jsonify({'message': 'Place deleted successfully'})

@app.route('/warehouse', methods=['POST'])
@login_required
def add_warehouse_item():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    item_name = data.get('item_name')
    quantity = data.get('quantity')

    if not isinstance(item_name, str) or not item_name.strip():
        return jsonify({'error': 'Valid item name required'}), 400

    if not isinstance(quantity, int) or quantity < 0:
        return jsonify({'error': 'Quantity must be a non-negative integer'}), 400
        
    conn = get_db_connection('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO warehouse_inventory (item_name, quantity) VALUES (?, ?)''', (item_name.strip(), quantity))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Item added to warehouse successfully', 'warehouse_id': new_id}), 201

@app.route('/warehouse/<int:warehouse_id>', methods=['PUT'])
@login_required
def update_warehouse_item(warehouse_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    item_name = data.get('item_name')
    quantity = data.get('quantity')


    if not isinstance(item_name, str) or not item_name.strip():
        return jsonify({'error': 'Valid item name required'}), 400

    if type(quantity) is not int or quantity < 0:
        return jsonify({'error': 'Quantity must be a non-negative integer'}), 400

    

    conn = get_db_connection('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE warehouse_inventory SET item_name = ?, quantity = ? WHERE warehouse_id = ?''', (item_name.strip(), quantity, warehouse_id))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()

    if updated_rows == 0:
        return jsonify({'error': 'Item not found'}), 404
    
    

    return jsonify({
      'message': 'Item updated successfully','warehouse_id': warehouse_id,
      'quantity': quantity
    }), 200
    

@app.route('/warehouse/<int:warehouse_id>', methods=['DELETE'])
@login_required
def delete_warehouse_item(warehouse_id):
    conn = get_db_connection('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM warehouse_inventory WHERE warehouse_id = ?''', (warehouse_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()

    if deleted_rows == 0:
        return jsonify({'error': 'Item not found'}), 404

    return jsonify({'message': 'Item deleted successfully', 'warehouse_id': warehouse_id}), 200



REQUEST_STATUSES = {'pending', 'approved', 'fulfilled', 'rejected'}


@app.route('/requests', methods=['GET'])
@login_required
def get_requests():
    connection = get_db_connection('requests.db')
    requests = connection.execute(
        '''SELECT request_id, account_id, item_name, quantity, status, created_at
           FROM requests ORDER BY created_at DESC, request_id DESC'''
    ).fetchall()
    connection.close()
    return jsonify([dict(item) for item in requests])


@app.route('/requests', methods=['POST'])
@login_required
def add_request():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    item_name = data.get('item_name')
    quantity = data.get('quantity')
    if not isinstance(item_name, str) or not item_name.strip():
        return jsonify({'error': 'Valid item name required'}), 400
    if type(quantity) is not int or quantity <= 0:
        return jsonify({'error': 'Quantity must be a positive integer'}), 400

    connection = get_db_connection('requests.db')
    cursor = connection.cursor()
    cursor.execute(
        '''INSERT INTO requests (account_id, item_name, quantity)
           VALUES (?, ?, ?)''',
        (session['account_id'], item_name.strip(), quantity),
    )
    connection.commit()
    request_id = cursor.lastrowid
    connection.close()
    return jsonify({'message': 'Request created successfully', 'request_id': request_id}), 201


@app.route('/requests/<int:request_id>', methods=['GET'])
@login_required
def get_request(request_id):
    connection = get_db_connection('requests.db')
    item = connection.execute(
        '''SELECT request_id, account_id, item_name, quantity, status, created_at
           FROM requests WHERE request_id = ?''',
        (request_id,),
    ).fetchone()
    connection.close()
    if not item:
        return jsonify({'error': 'Request not found'}), 404
    return jsonify(dict(item))


@app.route('/requests/<int:request_id>', methods=['PUT'])
@login_required
def update_request(request_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    item_name = data.get('item_name')
    quantity = data.get('quantity')
    status = data.get('status')
    if not isinstance(item_name, str) or not item_name.strip():
        return jsonify({'error': 'Valid item name required'}), 400
    if type(quantity) is not int or quantity <= 0:
        return jsonify({'error': 'Quantity must be a positive integer'}), 400
    if not isinstance(status, str) or status not in REQUEST_STATUSES:
        return jsonify({'error': 'Valid request status required'}), 400

    connection = get_db_connection('requests.db')
    cursor = connection.cursor()
    cursor.execute(
        '''UPDATE requests SET item_name = ?, quantity = ?, status = ?
           WHERE request_id = ?''',
        (item_name.strip(), quantity, status, request_id),
    )
    connection.commit()
    updated_rows = cursor.rowcount
    connection.close()
    if updated_rows == 0:
        return jsonify({'error': 'Request not found'}), 404
    return jsonify({'message': 'Request updated successfully', 'request_id': request_id}), 200


@app.route('/requests/<int:request_id>', methods=['DELETE'])
@login_required
def delete_request(request_id):
    connection = get_db_connection('requests.db')
    cursor = connection.cursor()
    cursor.execute('DELETE FROM requests WHERE request_id = ?', (request_id,))
    connection.commit()
    deleted_rows = cursor.rowcount
    connection.close()
    if deleted_rows == 0:
        return jsonify({'error': 'Request not found'}), 404
    return jsonify({'message': 'Request deleted successfully', 'request_id': request_id}), 200


if __name__ == '__main__':
    if is_production:
        raise RuntimeError('Use Gunicorn to run the application in production')
    app.run(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', '5001')),
        debug=app.config['DEBUG'],
    )