from app import mongo
import datetime

def create_order(user_id, product_ids, total_price):
    order = {
        "user_id": user_id,
        "products": product_ids,
        "total_price": total_price,
        "status": "Pending",
        "created_at": datetime.datetime.now()
    }
    return mongo.db.orders.insert_one(order).inserted_id
