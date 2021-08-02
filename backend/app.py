import hmac
import sqlite3
import datetime

from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# database and user selection


def sign_in_users():
    with sqlite3.connect('products.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


users = sign_in_users()

# initialisation of the user table


def signed_in_users_table():
    conn = sqlite3.connect('products.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()
# registration of new members


def registration_table():
    with sqlite3.connect('products.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS user_registration(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "first_name TEXT NOT NULL,"
                     "last_name TEXT NOT NULL,"
                     "username TEXT NOT NULL,"
                     "password TEXT NOT NULL)")
        print("register table created successfully")


# initialisation of the product table


def product_table():
    with sqlite3.connect('products.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS product (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "title TEXT NOT NULL,"
                     "name TEXT NOT NULL,"
                     "price INT NOT NULL"
                     "quantity INT NOT NULL)")
    print("product table created successfully.")


signed_in_users_table()
registration_table()
product_table()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("products.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user_registration("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
        return response

# inserting the products that are chosen


@app.route('/products/', methods=["POST"])
@jwt_required()
def create_products():
    response = {}

    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        date_created = datetime.datetime.now()

        with sqlite3.connect('products.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO product("
                           "title,"
                           "content,"
                           "date_created) VALUES(?, ?, ?)", (title, content, date_created))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "Blog post added successfully"
        return response


@app.route('/get-products/', methods=["GET"])
def get_products():
    response = {}
    with sqlite3.connect("products.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products ")

        posts = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = posts
    return response


@app.route("/delete-post/<int:post_id>")
@jwt_required()
def delete_products(product_id):
    response = {}
    with sqlite3.connect("products.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM  WHERE id=" + str(product_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = " product deleted successfully."
    return response


@app.route('/edit-post/<int:post_id>/', methods=["PUT"])
@jwt_required()
def update_post(product_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('products.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("title") is not None:
                put_data["title"] = incoming_data.get("title")
                with sqlite3.connect('products.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE product SET title =? WHERE id=?", (put_data["title"], product_id))
                    conn.commit()
                    response['message'] = "Update was successfully"
                    response['status_code'] = 200
            if incoming_data.get("content") is not None:
                put_data['content'] = incoming_data.get('content')

                with sqlite3.connect('products.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE product SET content =? WHERE id=?", (put_data["content"], product_id))
                    conn.commit()

                    response["content"] = "product updated successfully"
                    response["status_code"] = 200
    return response


@app.route('/get-post/<int:post_id>/', methods=["GET"])
def get_post(product_id):
    response = {}

    with sqlite3.connect("products.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product WHERE id=" + str(product_id))

        response["status_code"] = 200
        response["description"] = "Products retrieved successfully"
        response["data"] = cursor.fetchone()

    return jsonify(response)


if __name__ == "__main__":
    debug = True
    app.run()
