from services.order_service import process_order
from data.products import products

def run_tests():
    
    print("\n--- Test 1: Valid Order ---")
    order = {"order_id": "O1001", "items": [
        {"product_id": "P1", "quantity": 2},
        {"product_id": "P2", "quantity": 5}
    ]}
    print(process_order(products, order))

    print("\n--- Test 2: Product Does Not Exist ---")
    order = {"order_id": "O1002", "items": [
        {"product_id": "P99", "quantity": 1}
    ]}
    print(process_order(products, order))

    print("\n--- Test 3: Insufficient Stock ---")
    order = {"order_id": "O1003", "items": [
        {"product_id": "P1", "quantity": 999}
    ]}
    print(process_order(products, order))

    print("\n--- Test 4: Duplicate Product ---")
    order = {"order_id": "O1004", "items": [
        {"product_id": "P1", "quantity": 1},
        {"product_id": "P1", "quantity": 2}
    ]}
    print(process_order(products, order))

    print("\n--- Test 5: Empty Order ---")
    order = {"order_id": "O1005", "items": []}
    print(process_order(products, order))

if __name__ == "__main__":
    run_tests()