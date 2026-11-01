from flask import Flask, request, jsonify
from flask_cors import CORS

from database import (
    create_db_table,
    insert_user,
    get_users,
    get_user_by_id,
    update_user,
    delete_user,
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# Returns all users.
@app.route('/api/users', methods=['GET'])
def api_get_users():
    return jsonify(get_users())


# Returns one user by id.
@app.route('/api/users/<user_id>', methods=['GET'])
def api_get_user(user_id):
    return jsonify(get_user_by_id(user_id))


# Adds the user sent in the request body.
@app.route('/api/users/add', methods=['POST'])
def api_add_user():
    user = request.get_json()
    return jsonify(insert_user(user))


# Updates the user sent in the request body.
@app.route('/api/users/update', methods=['PUT'])
def api_update_user():
    user = request.get_json()
    return jsonify(update_user(user))


# Deletes a user by id.
@app.route('/api/users/delete/<user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    return jsonify(delete_user(user_id))


if __name__ == "__main__":
    create_db_table()
    app.run()
