import hmac
import sqlite3
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, render_template
from flask_jwt import JWT, jwt_required, current_identity
from smtplib import SMTPRecipientsRefused, SMTPAuthenticationError
from flask_cors import CORS


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# Creating User_table
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


# Creating Post_table
def login_table():
    with sqlite3.connect('POS.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS login (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "user_email TEXT NOT NULL,"
                     "password TEXT NOT NULL,"
                     "login_date TEXT NOT NULL)")
    print("Login table created successfully.")


# Creating product_table
def products_table():
    with sqlite3.connect('POS.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "product_name TEXT NOT NULL,"
                     "price INTEGER NOT NULL,"
                     "description TEXT NOT NULL,"
                     "images TEXT NOT NULL)")
    print("Product table created successfully.")


# Tables
products_table()
user_table()
login_table()



# Function to Fetch Everything from the user Table


def fetch_users():
    with sqlite3.connect('POS.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")

        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data




users = fetch_users()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


# authentication of username and password to get access token
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

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'sithandathuzipho@gmail.com'
app.config['MAIL_PASSWORD'] = 'Crf6ZS@#'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
Mail = Mail(app)

jwt = JWT(app, authenticate, identity)


# end-point route for authorization
@app.route('/protected')
def protected():
    return '%s' % current_identity


@app.route('/login/', methods=['GET', 'POST'])
def login():
    return render_template('/login.html')


# end-point route for all registrations
@app.route('/user-registration/', methods=["POST"])
def new_member_registration():
    response = {}

    #try:
    if request.method == "POST":
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            address = request.form['address']
            user_email = request.form['user_email']
            username = request.form['username']
            password = request.form['password']
            phone_number = request.form['phone_number']

            with sqlite3.connect('POS.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO user("
                               "first_name,"
                               "last_name,"
                               "address,"
                               "user_email,"
                               "username,"
                               "phone_number,"
                               "password) VALUES(?, ?, ?, ?, ?, ?, ?)",
                               (first_name, last_name, address, user_email, username, password, phone_number))
                conn.commit()

                response["message"] = "success"
                response["status_code"] = 201
                msg = Message("Thank you for Registering !!", sender="sithandathuzipho@gmail.com", recipients=[user_email])
                msg.body = "You have successfully registered an account"
                Mail.send(msg)
            return response
   # except SMTPRecipientsRefused:
        #response["message"] = "Invalid email!, Try again"
       # response["status_code"] = 400
       # return response
   # except SMTPAuthenticationError:
      #  response["message"] = "Invalid! Use valid username and password"
      #  response["status_code"] = 400
      #  return response


# end-point route to create products
@app.route('/create-products/', methods=["POST"])
#@jwt_required()
def create_products():
    response = {}

    if request.method == "POST":
        product_name = request.form['product_name']
        price = request.form['price']
        description = request.form['description']
        images = request.form['images']

        with sqlite3.connect('POS.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products("
                           "product_name,"
                           "price,"
                           "description, images ) VALUES(?, ?, ?, ?)", (product_name, price, description, images))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "products created successfully"
        return response

@app.route('/get-users/',methods=['GET'])
def all_users():
    response = {}
    with sqlite3.connect("POS.db") as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute("SELECT * FROM user")
        posts = cursor.fetchall()
        accumulator = []
        for i in posts:
            accumulator.append({k: i[k] for k in i.keys()})
            response['status_code'] = 200
            response['data'] = tuple(accumulator)
            return jsonify(response)


# Creating products
@app.route('/products/')
def display_products():
    products = [{'id': 0, 'Product_name': 'Hoodie', 'Price': 500, 'Description': 'Look nice and warm this winter with this warm hoodies'},
                {'id': 1, 'Product_name': 'Dress', 'Price': 300, 'Description': ' Lovely slit dress with buttons'},
                {'id': 2, 'Product_name': 'Iphone', 'Price': 3000, 'Description': 'Smartphone'}]
    return jsonify(products)


# end-point products
@app.route('/get-Point-Of-Sale/', methods=["GET"])
def get_POS():
    response = {}
    with sqlite3.connect("POS.db") as conn:  # connecting to the database
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute("SELECT * FROM products")  # selecting from user_products table
        posts = cursor.fetchall()
        accumulator = []

        for i in posts:
            accumulator.append({k: i[k] for k in i.keys()})

    response['status_code'] = 200
    response['data'] = tuple(accumulator)
    return jsonify(response)


# route to delete products
@app.route("/delete-products/<int:post_id>")
@jwt_required()
def delete_post(post_id):
    response = {}
    with sqlite3.connect("POS.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=" + str(post_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "products deleted successfully."
    return response


# route to update products
@app.route('/update_products/<int:post_id>/', methods=["PUT"])
@jwt_required()
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
                    cursor.execute("UPDATE products SET product_name =? WHERE id=?", (put_data["product_name"], post_id))

                    conn.commit()
                    response['message'] = "product_name Updated successfully"
                    response['status_code'] = 200

        # updating price
            if incoming_data.get("price") is not None:
                put_data['price'] = incoming_data.get('price')

                with sqlite3.connect('POS.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET price =? WHERE id=?", (put_data["price"], post_id))
                    conn.commit()

                    response["price"] = "price updated successfully"
                    response["status_code"] = 200

        # updating description
            if incoming_data.get("description") is not None:
                put_data['description'] = incoming_data.get('description')

                with sqlite3.connect('POS.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET description =? WHERE id=?", (put_data["description"], post_id))
                    conn.commit()

                    response["price"] = "description updated successfully"
                    response["status_code"] = 200

             # updating images
            if incoming_data.get("images") is not None:
                put_data['images'] = incoming_data.get('images')

                with sqlite3.connect('POS.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET images =? WHERE id=?", (put_data["images"], post_id))
                    conn.commit()

                    response["images"] = "images updated successfully"
                    response["status_code"] = 200


    return response


if __name__ == '__main__':
    app.run(debug=True)