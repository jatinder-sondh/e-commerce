from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from bson import ObjectId 
from datetime import datetime
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import stripe
import secrets
import requests


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/ecommerce_db"
mongo = PyMongo(app)
users_collection = mongo.db.users

# Initialize Flask-Bcrypt for password hashing
bcrypt = Bcrypt(app)


# Secret key for sessions
app.secret_key = secrets.token_hex(16)

# Stripe API key setup
stripe.api_key = 'your-stripe-api-key'  # Set your Stripe key here



@app.route('/home')
def home():
    search_query = request.args.get('search')  # Capture the search query
    if search_query:
        # Search for products whose name or description contains the search query (case-insensitive)
        products = list(mongo.db.products.find({
            '$or': [
                {'name': {'$regex': search_query, '$options': 'i'}},
                {'description': {'$regex': search_query, '$options': 'i'}}
            ]
        }))
    else:
        products = mongo.db.products.find()  
    
    product_list = list(products)
    return render_template('home.html', products=product_list)

@app.route('/')
def main_page():
    if mongo.db.products.count_documents({}) == 0:
        print("No products found in the database. Loading products...")
        # Load products from the API
        fetch_and_add_products()  
    else:
        print("Products already exist in the database.")
    return render_template('main.html')


def fetch_and_add_products():
    API_URL = "https://fakestoreapi.com/products"
    response = requests.get(API_URL)
    
    # Check if the request was successful
    if response.status_code == 200:
        products = response.json()  # Parse the response JSON into a Python list
        
        # Format products if necessary (you can customize this to match your schema)
        formatted_products = [
            {
                "name": product["title"],
                "description": product["description"],
                "price": product["price"],
                "category": product["category"],
                "stock": 100,  # You can set a fixed stock value or adjust it
                "image": product["image"],
                "rating": product["rating"]["rate"] if "rating" in product else 4.0,  # Default to 4.0 if no rating exists
            }
            for product in products
        ]
        
        # Insert products into the MongoDB collection
        mongo.db.products.insert_many(formatted_products)
        print(f"Successfully added {len(formatted_products)} products to the database!")
    else:
        print("Failed to fetch products from the API!")


@app.route('/product_detail/<string:id>', methods=['GET', 'POST'])
def product_detail(id):
    product = mongo.db.products.find_one({'_id': ObjectId(id)})
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    try:
        # Check if the provided product_id is a valid ObjectId
        product_obj_id = ObjectId(product_id)
    except InvalidId:
        return "Invalid Product ID", 400

    # Query the product to ensure it exists
    product = mongo.db.products.find_one({'_id': product_obj_id})

    if not product:
        return "Product not found", 404

    # If the cart doesn't exist in the session, initialize it
    if 'cart' not in session:
        session['cart'] = []

    # Add only the product ID to the cart
    session['cart'].append(str(product['_id']))  # Store product ID as a string
    session.modified = True

    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_product_ids = session.get('cart', [])
    
    # Convert the list of IDs to ObjectIds
    object_ids = [ObjectId(pid) for pid in cart_product_ids]

    # Fetch products from the database
    products = list(mongo.db.products.find({'_id': {'$in': object_ids}}))

    return render_template('cart.html', products=products)

@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    cart_product_ids = session.get('cart', [])

    # Check if the product ID exists in the cart
    if product_id in cart_product_ids:
        cart_product_ids.remove(product_id)  # Remove the specific product ID
    
    # Update the session with the modified cart
    session['cart'] = cart_product_ids
    session.modified = True  # Mark the session as modified to save changes

    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        cart_product_ids = session.get('cart', [])
        object_ids = [ObjectId(pid) for pid in cart_product_ids]
        products = list(mongo.db.products.find({'_id': {'$in': object_ids}}))

        total_price = sum(product['price'] for product in products)

        order = {
            'customer_name': customer_name,
            'address': address,
            'email': email,
            'phone': phone,
            'products': products,
            'total_price': total_price,
            'status': 'Pending',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        mongo.db.orders.insert_one(order)
        session.pop('cart', None)
        return redirect(url_for('confirmation', order_id=str(order['_id'])))

    # If GET request, display the checkout page
    cart_product_ids = session.get('cart', [])
    object_ids = [ObjectId(pid) for pid in cart_product_ids]
    products = list(mongo.db.products.find({'_id': {'$in': object_ids}}))
    total_price = sum(product['price'] for product in products)

    return render_template('checkout.html', products=products, total_price=total_price)

@app.route('/confirmation/<order_id>')
def confirmation(order_id):
    order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
    if not order:
        return "Order not found", 404

    return render_template('confirmation.html', order=order)

@app.route('/orders')
def orders():
    # user_email = session.get('user_email', None)
    # if not user_email:
    #     return redirect(url_for('login'))  # Redirect to login if user is not authenticated
    
    orders = mongo.db.orders.find()  
    user_orders = list(orders)

    for order in user_orders:
        order['_id'] = str(order['_id'])

    return render_template('orders.html', orders=user_orders)

@app.route('/order_details/<order_id>')
def order_details(order_id):
    order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})

    if not order:
        return "Order not found", 404

    return render_template('order_details.html', order=order)

if __name__ == "__main__":
    app.run(debug=True)
