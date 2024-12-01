from app import mongo

def get_all_products():
    return mongo.db.products.find()

def get_product_by_id(product_id):
    return mongo.db.products.find_one({"_id": product_id})
