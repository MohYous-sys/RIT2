
from flask import Flask, jsonify, request, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
import os
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

def get_db_connection():
    connection = sqlite3.connect('accounts.db')
    connection.row_factory = sqlite3.Row
    return connection   

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
    cursor.execute('''SELECT id, password, admin FROM accounts WHERE name = ?''', (name.strip(),))
    account = cursor.fetchone()
    conn.close()

    if not account:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not check_password_hash(account['password'], password.strip()):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['account_id'] = account['id']
    session['role'] = 'Admin' if account['admin'] == 1 else 'Regular User'

    return jsonify({'message': 'Login successful', 'account_id': account['id'], 'role': session['role']}), 200

@app.route('/')
def home():
    return "Warehouse Management System"

@app.route('/accounts', methods=['GET'])
def get_accounts():
    conn = get_db_connection()
    accounts = conn.execute('SELECT id, name, admin FROM accounts').fetchall()
    conn.close()

    return jsonify([dict(account) for account in accounts])

@app.route('/accounts', methods=['POST'])
def add_account():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    name = data.get('name')
    password = data.get('password')
    admin = 0

    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': 'Valid name required'}), 400

    if not isinstance(password, str) or not password.strip():
        return jsonify({'error': 'Valid password required'}), 400

    

    hashed_password = generate_password_hash(password.strip(), method='pbkdf2:sha256')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO accounts (name, password, admin) VALUES (?, ?, ?)''', (name.strip(), hashed_password, admin))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Account created successfully', 'account_id': new_id}), 201



@app.route('/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
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
    conn.close()

    return jsonify({'message': 'Account updated successfully', 'account_id': account_id}), 200

@app.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM accounts WHERE id = ?''', (account_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()

    if deleted_rows == 0:
        return jsonify({'error': 'Account not found'}), 404

    return jsonify({'message': 'Account deleted successfully', 'account_id': account_id}), 200

@app.route('/warehouse', methods=['GET'])
def get_warehouse():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    
    items = conn.execute('SELECT warehouse_id, item_name, quantity FROM warehouse_inventory').fetchall()
    conn.close()

    return jsonify([dict(item) for item in items])

@app.route('/places', methods=['GET'])
def get_places():
    conn = sqlite3.connect('places.db')
    conn.row_factory = sqlite3.Row
    
    places = conn.execute('SELECT place_id, value_per_item FROM places').fetchall()
    conn.close()

    return jsonify([dict(place) for place in places])

@app.route('/places', methods=['POST'])
def add_place():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    value_per_item = data.get('value_per_item')

    if not isinstance(value_per_item, (int, float)) or value_per_item < 0:
        return jsonify({'error': 'Valid value per item required'}), 400

    conn = sqlite3.connect('places.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO places (value_per_item) VALUES (?)''', (value_per_item,))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Place added successfully', 'place_id': new_id}), 201

@app.route('/places/<int:place_id>', methods=['PUT'])
def update_place(place_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    value_per_item = data.get('value_per_item')

    if not isinstance(value_per_item, (int, float)) or value_per_item < 0:
        return jsonify({'error': 'Valid value per item required'}), 400

    conn = sqlite3.connect('places.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE places SET value_per_item = ? WHERE place_id = ?''', (value_per_item, place_id))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()

    if updated_rows == 0:
        return jsonify({'error': 'Place not found'}), 404

    return jsonify({'message': 'Place updated successfully'})

@app.route('/places/<int:place_id>', methods=['DELETE'])
def delete_place(place_id):
    conn = sqlite3.connect('places.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM places WHERE place_id = ?''', (place_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()

    if deleted_rows == 0:
        return jsonify({'error': 'Place not found'}), 404

    return jsonify({'message': 'Place deleted successfully'})

@app.route('/warehouse', methods=['POST'])
def add_warehouse_item():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    account_id = data.get('account_id')

    if not isinstance(account_id, int):
        return jsonify({'error': 'Valid account_id required'}), 400
    
    conn = get_db_connection()
    account = conn.execute('SELECT admin FROM accounts WHERE id = ?', (account_id,)).fetchone()
    conn.close()

    if not account or account['admin'] != 1:
        return jsonify({'error': 'Admin access required'}), 403

   

    item_name = data.get('item_name')
    quantity = data.get('quantity')

    if not isinstance(item_name, str) or not item_name.strip():
        return jsonify({'error': 'Valid item name required'}), 400

    if not isinstance(quantity, int) or quantity < 0:
        return jsonify({'error': 'Quantity must be a non-negative integer'}), 400
        
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO warehouse_inventory (item_name, quantity) VALUES (?, ?)''', (item_name.strip(), quantity))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Item added to warehouse successfully', 'warehouse_id': new_id}), 201

@app.route('/warehouse/<int:warehouse_id>', methods=['PUT'])
def update_warehouse_item(warehouse_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON data'}), 400

    item_name = data.get('item_name')
    quantity = data.get('quantity')


    if type(quantity) is not int or quantity < 0:
        return jsonify({'error': 'Quantity must be a non-negative integer'}), 400

    

    conn = sqlite3.connect('warehouse.db')
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
def delete_warehouse_item(warehouse_id):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM warehouse_inventory WHERE warehouse_id = ?''', (warehouse_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()

    if deleted_rows == 0:
        return jsonify({'error': 'Item not found'}), 404

    return jsonify({'message': 'Item deleted successfully', 'warehouse_id': warehouse_id}), 200



if __name__ == '__main__':
    app.run(debug=True, port=5001)