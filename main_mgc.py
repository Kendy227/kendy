import base64
import requests
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# Flask app for handling callbacks
app = Flask(__name__)

# Replace with your actual Partner ID and Secret Key
partner_id = "d2c1ab6c0b58488fbd1ee0d7de0511e9"
secret_key = "ha61HJLMhO"

# Generate the Basic Auth value
auth_string = f"{partner_id}:{secret_key}"
auth_bytes = auth_string.encode("utf-8")
auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

# Telegram Bot Token
BOT_TOKEN = "7808979418:AAGEtK53sjJ76aX1OlkzYDdslYLeewA6vhE"

# Function to retrieve order details
def get_order_detail(order_id):
    api_url = f"https://moogold.com/wp-json/v1/api/order/{order_id}"
    headers = {"Authorization": f"Basic {auth_base64}"}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to retrieve order details. Status Code: {response.status_code}"}

# Function to retrieve order details by partner order ID
def get_order_detail_by_partner_order_id(partner_order_id):
    api_url = "https://moogold.com/wp-json/v1/api/order/order_detail_partner_id"
    headers = {"Authorization": f"Basic {auth_base64}"}
    payload = {"partner_order_id": partner_order_id}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Order Details Retrieved Successfully:")
        print(response.json())
    else:
        print(f"Failed to retrieve order details. Status Code: {response.status_code}")
        print(f"Response: {response.text}")

# Function to list products by category
def list_products_by_category(category_id):
    api_url = f"https://moogold.com/wp-json/v1/api/product/list/{category_id}"
    headers = {"Authorization": f"Basic {auth_base64}"}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to retrieve products. Status Code: {response.status_code}"}

# Function to get product details
def get_product_detail(product_id):
    api_url = f"https://moogold.com/wp-json/v1/api/product/detail/{product_id}"
    headers = {"Authorization": f"Basic {auth_base64}"}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        print("Product Details Retrieved Successfully:")
        print(response.json())
    else:
        print(f"Failed to retrieve product details. Status Code: {response.status_code}")
        print(f"Response: {response.text}")

# Function to get product server list
def get_product_server_list(product_id):
    api_url = f"https://moogold.com/wp-json/v1/api/product/server_list/{product_id}"
    headers = {"Authorization": f"Basic {auth_base64}"}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        print("Server List Retrieved Successfully:")
        print(response.json())
    else:
        print(f"Failed to retrieve server list. Status Code: {response.status_code}")
        print(f"Response: {response.text}")

# Function to validate a product
def validate_product(product_id, server_id, quantity):
    api_url = "https://moogold.com/wp-json/v1/api/product/validate"
    headers = {"Authorization": f"Basic {auth_base64}"}
    payload = {"product_id": product_id, "server_id": server_id, "quantity": quantity}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"API Response: {response.json()}")
        print(f"API Response: {response.json()}")
        return response.json()
    else:
        return {"error": f"Failed to validate product. Status Code: {response.status_code}"}

# Function to retrieve wallet balance
def get_wallet_balance():
    api_url = "https://moogold.com/wp-json/v1/api/balance"
    headers = {"Authorization": f"Basic {auth_base64}"}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to retrieve wallet balance. Status Code: {response.status_code}"}

# Function to reload wallet balance
def reload_wallet_balance(payment_method, amount):
    api_url = "https://moogold.com/wp-json/v1/api/reload_balance"
    headers = {"Authorization": f"Basic {auth_base64}"}
    payload = {"payment_method": payment_method, "amount": amount}
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to reload wallet balance. Status Code: {response.status_code}"}

# Callback handler
@app.route('/callback', methods=['POST'])
def handle_callback():
    data = request.get_json()
    status = data.get('status')
    message = data.get('message')
    account_details = data.get('account_details')
    order_id = data.get('order_id')
    total = data.get('total')
    print(f"Callback received: {data}")
    response = {"status": "success", "message": "Callback processed successfully"}
    return jsonify(response), 200

# Telegram bot command handlers
def telegram_get_order_detail(update: Update, context: CallbackContext):
    order_id = context.args[0] if context.args else None
    if not order_id:
        update.message.reply_text("Please provide an order ID.")
        return
    result = get_order_detail(order_id)
    update.message.reply_text(result)

def telegram_get_wallet_balance(update: Update, context: CallbackContext):
    result = get_wallet_balance()
    update.message.reply_text(result)

def telegram_reload_wallet_balance(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Usage: /reload <payment_method> <amount>")
        return
    payment_method = context.args[0]
    amount = context.args[1]
    result = reload_wallet_balance(payment_method, amount)
    update.message.reply_text(result)

def telegram_validate_product(update: Update, context: CallbackContext):
    if len(context.args) < 3:
        update.message.reply_text("Usage: /validate <product_id> <server_id> <quantity>")
        return
    product_id = context.args[0]
    server_id = context.args[1]
    quantity = context.args[2]
    result = validate_product(product_id, server_id, quantity)
    update.message.reply_text(result)

def telegram_list_products_by_category(update: Update, context: CallbackContext):
    category_id = context.args[0] if context.args else None
    if not category_id:
        update.message.reply_text("Please provide a category ID.")
        return
    result = list_products_by_category(category_id)
    update.message.reply_text(result)

def start(update: Update, context: CallbackContext):
    print(f"Received /start command from {update.effective_user.username}")
    update.message.reply_text("Bot is working!")

def ping(update: Update, context: CallbackContext):
    update.message.reply_text("Pong!")

from telegram.ext import Application, CommandHandler

# Main function to start the bot
def main():
    # Create the Application instance
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("order", telegram_get_order_detail))
    application.add_handler(CommandHandler("balance", telegram_get_wallet_balance))
    application.add_handler(CommandHandler("reload", telegram_reload_wallet_balance))
    application.add_handler(CommandHandler("validate", telegram_validate_product))
    application.add_handler(CommandHandler("products", telegram_list_products_by_category))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping))

    # Start the bot
    print("Starting Telegram bot...")
    application.run_polling()

# Flask app runner
if __name__ == '__main__':
    # Start the Telegram bot
    main()