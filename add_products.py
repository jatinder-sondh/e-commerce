import requests
from flask import Flask
from flask_pymongo import PyMongo

# Flask app setup
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://jatinder090198:4y7gpu01HIM7aufN@cluster0.nuzal.mongodb.net/ecommerce_db?retryWrites=true&w=majority&appName=Cluster0"
mongo = PyMongo(app)

# API URL for random products (Fake Store API)
API_URL = "https://fakestoreapi.com/products"

def fetch_and_add_products():
    # Fetch products from the API
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

if __name__ == "__main__":
    with app.app_context():  # Ensure the app context is active when running this script
        fetch_and_add_products()
