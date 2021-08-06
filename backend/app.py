import hmac
import sqlite3

from flask import Flask, request, jsonify
from flask_jwt import JWT, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message


class User(object):
    def __init__(self, id, username, password, user_email, phone_number, address):
        self.id = id
        self.username = username
        self.password = password
        self.user_email = user_email
        self.phone_number = phone_number
        self.address = address


# Initialisation of the users table


def user_table():
    conn = sqlite3.connect('POS.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL, address TEXT NOT NULL, phone_number INT NOT NULL, user_email TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()

# users that logged in


def login_table():
    with sqlite3.connect('POS.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS login (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "user_email TEXT NOT NULL,"
                     "password TEXT NOT NULL,"
                     "login_date TEXT NOT NULL)")
    print("Login table created successfully.")


def products_table():
    with sqlite3.connect('POS.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS products_table (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "product_name TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "description TEXT NOT NULL)")
    print("Product table created successfully.")


products_table()
user_table()
login_table()

# fetching the users from the user table


def fetch_users():
    with sqlite3.connect('POS.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4], data[5], data[6], data[7]))
    return new_data


users = fetch_users()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

# the process  of verifying the identity of a user.


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
jwt = JWT(app, authenticate, identity)
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 456
app.config['MAIL_USERNAME'] = 'Retshepilekoloko27@gmail.com'
app.config['MAIL_PASSWORD'] = 'retsepile2021'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
Mail = Mail(app)

# when the user enters they details it will be protected from the third party


@app.route('/protected')
def protected():
    return '%s' % current_identity


@app.route('/login/', methods=['GET', 'POST'])
def login():
    response = {}
    return response

# creating a function for people who would want to register for an account


@app.route('/user-registration/', methods=["POST"])
def new_member_registration():
    response = {}

    if request.method == "POST":

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        phone_number = request.form['phone_number']
        user_email = request.form['user_email']

        with sqlite3.connect("POS.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password,address,phone_number,user_email) VALUES(?, ?, ?, ?, ?, ?, ?)", (first_name,
                                                                                                     last_name,
                                                                                                     username,
                                                                                                     password,
                                                                                                     address,
                                                                                                     phone_number,
                                                                                                     user_email))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201

            msg = Message('Hello from the other side', sender='Retshepilekoloko27@gmail.com',
                          recipients=['Retshepilekoloko27@gmail.com'])
            msg.body = "Hey Paul, sending you this email from my Flask app, lmk if it works"
            Mail.send(msg)
        return response

# will insert products that will be sold


@app.route('/create-products/', methods=["POST"])
def create_products():
    response = {}

    if request.method == "POST":
        product_name = request.form['product_name']
        price = request.form['price']
        description = request.form['description']
        with sqlite3.connect('POS.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products_table("
                           "product_name,"
                           "price,"
                           "description) VALUES(?, ?, ?)", (product_name, price, description))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "products created successfully"
        return response

# Creating products


@app.route('/all_products/')
def display_products():
    products = [{'id': 0, 'Product_name': 'Hoodie', 'Price': 500, 'Description': 'Look nice and warm this winter with this warm hoodies'},
                {'id': 1, 'Product_name': 'Dress', 'Price': 300, 'Description': ' Lovely slit dress with buttons'},
                {'id': 2, 'Product_name': 'Iphone', 'Price': 3000, 'Description': 'Smartphone'}]
    return jsonify(products)

# getting the point of sales product from products


@app.route('/get_Point_of_Sales/', methods=["GET"])
def get_P_O_S():
    response = {}
    with sqlite3.connect("POS.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products_table")

        posts = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = posts
    return response

# deleting of some products that will probably be out of stock or have gotten rotten


@app.route("/delete-products/<int:post_id>")
def delete_post(post_id):
    response = {}
    with sqlite3.connect("POS.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products_table WHERE id=" + str(post_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "products deleted successfully."
    return response

# modifying some of the product prices and adding new products


# route to update products

@app.route('/update_products/<int:post_id>/', methods=["PUT"])
def modify_product(post_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('POS.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

        # updating product_name
            if incoming_data.get("product_name") is not None:
                put_data["product_name"] = incoming_data.get("product_name")
                with sqlite3.connect('POS.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE user_products SET product_name =? WHERE id=?", (put_data["product_name"],
                                                                                           post_id))
                    conn.commit()
                    response['message'] = "product_name Updated successfully"
                    response['status_code'] = 200

        # updating price
            if incoming_data.get("price") is not None:
                put_data['price'] = incoming_data.get('price')

                with sqlite3.connect('POS.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE user_products SET price =? WHERE id=?", (put_data["price"], post_id))
                    conn.commit()

                    response["price"] = "price updated successfully"
                    response["status_code"] = 200

        # updating description
            if incoming_data.get("description") is not None:
                put_data['description'] = incoming_data.get('description')

                with sqlite3.connect('POS.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE user_products SET description =? WHERE id=?", (put_data["description"],
                                                                                          post_id))
                    conn.commit()

                    response["price"] = "description updated successfully"
                    response["status_code"] = 200
    return response


@app.route('/get-post/<int:post_id>/', methods=["GET"])
def get_post(post_id):
    response = {}

    with sqlite3.connect("POS.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM post WHERE id=" + str(post_id))

        response["status_code"] = 200
        response["description"] = "Point of Sale post retrieved successfully"
        response["data"] = cursor.fetchone()

    return jsonify(response)


@app.route('/mailed/<string:email>', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        msg = Message('EMAIL ')


if __name__ == '__main__':
    app.run(debug=True)
