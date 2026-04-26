def success_response(order_id, updated_stock):
    return {
        "status": "success",
        "message": f"Order {order_id} processed successfully.",
        "updated_stock": updated_stock
    }

def error_response(message):
    return {
        "status": "error",
        "message": message
    }