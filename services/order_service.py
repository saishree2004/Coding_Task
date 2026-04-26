from utils.response import success_response, error_response

def process_order(products, order):
    
    # Build inventory lookup map
    inventory = {p["product_id"]: p.copy() for p in products}

    items    = order.get("items", [])
    order_id = order.get("order_id", "UNKNOWN")

    # Check 1 — Empty order
    if not items:
        return error_response(f"Order {order_id} has no items.")

    # Check 2 — Duplicate products
    seen_ids = set()
    for item in items:
        pid = item["product_id"]
        if pid in seen_ids:
            return error_response(f"Duplicate product ID '{pid}' in order {order_id}.")
        seen_ids.add(pid)

    # Check 3 & 4 — Product exists and stock is sufficient
    for item in items:
        pid = item["product_id"]
        qty = item["quantity"]

        if pid not in inventory:
            return error_response(f"Product ID '{pid}' does not exist.")

        available = inventory[pid]["stock"]
        if qty > available:
            return error_response(
                f"Insufficient stock for '{inventory[pid]['name']}'. "
                f"Requested: {qty}, Available: {available}."
            )

    # All checks passed — deduct stock
    for item in items:
        inventory[item["product_id"]]["stock"] -= item["quantity"]

    updated_stock = [
        {"product_id": p["product_id"], "name": p["name"], "stock": p["stock"]}
        for p in inventory.values()
    ]

    return success_response(order_id, updated_stock)