from flask_login import UserMixin
from pymongo import MongoClient
from bson import ObjectId 
# MongoDB connection setup
mongo = MongoClient('mongodb://localhost:27017/')
db = mongo['ecommerce_db']  # Replace with your database name

class User(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = user_id  # Required by Flask-Login
        self.username = username
        self.email = email

    @staticmethod
    def get_user_by_id(user_id):
        # Look for user by user_id in MongoDB
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            return User(
                user_id=str(user['_id']),
                username=user['username'],
                email=user['email']
            )
        return None

    @staticmethod
    def get_user_by_email(email):
        user = mongo.db.users.find_one({'email': email})
        if user:
            return User(
                user_id=str(user['_id']),
                username=user['username'],
                email=user['email']
            )
        return None
