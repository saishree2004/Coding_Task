import json
from data.products import products
from models.order import sample_order
from services.order_service import process_order
if __name__ == "__main__":
    result = process_order(products, sample_order)
    print(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))