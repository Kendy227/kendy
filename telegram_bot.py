import base64
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

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
def get_order_detail(update: Update, context: CallbackContext):
    order_id = context.args[0] if context.args else None
    if not order_id:
        update.message.reply_text("Please provide an order ID.")
        return

    api_url = f"https://moogold.com/wp-json/v1/api/order/{order_id}"
    headers = {"Authorization": f"Basic {auth_base64}"}
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        update.message.reply_text(f"Order Details: {response.json()}")
    else:
        update.message.reply_text(f"Failed to retrieve order details. Status Code: {response.status_code}")

# Function to retrieve wallet balance
def get_wallet_balance(update: Update, context: CallbackContext):
    api_url = "https://moogold.com/wp-json/v1/api/balance"
    headers = {"Authorization": f"Basic {auth_base64}"}
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        update.message.reply_text(f"Wallet Balance: {response.json()}")
    else:
        update.message.reply_text(f"Failed to retrieve wallet balance. Status Code: {response.status_code}")

# Function to reload wallet balance
def reload_wallet_balance(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Usage: /reload <payment_method> <amount>")
        return

    payment_method = context.args[0]
    amount = context.args[1]
    api_url = "https://moogold.com/wp-json/v1/api/reload_balance"
    headers = {"Authorization": f"Basic {auth_base64}"}
    payload = {"payment_method": payment_method, "amount": amount}
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        update.message.reply_text(f"Wallet Reloaded Successfully: {response.json()}")
    else:
        update.message.reply_text(f"Failed to reload wallet balance. Status Code: {response.status_code}")

# Function to validate a product
def validate_product(update: Update, context: CallbackContext):
    if len(context.args) < 3:
        update.message.reply_text("Usage: /validate <product_id> <server_id> <quantity>")
        return

    product_id = context.args[0]
    server_id = context.args[1]
    quantity = context.args[2]
    api_url = "https://moogold.com/wp-json/v1/api/product/validate"
    headers = {"Authorization": f"Basic {auth_base64}"}
    payload = {"product_id": product_id, "server_id": server_id, "quantity": quantity}
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        update.message.reply_text(f"Product Validation Successful: {response.json()}")
    else:
        update.message.reply_text(f"Failed to validate product. Status Code: {response.status_code}")

# Function to list products by category
def list_products_by_category(update: Update, context: CallbackContext):
    category_id = context.args[0] if context.args else None
    if not category_id:
        update.message.reply_text("Please provide a category ID.")
        return

    api_url = f"https://moogold.com/wp-json/v1/api/product/list/{category_id}"
    headers = {"Authorization": f"Basic {auth_base64}"}
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        update.message.reply_text(f"Products: {response.json()}")
    else:
        update.message.reply_text(f"Failed to retrieve products. Status Code: {response.status_code}")

# Main function to start the bot
def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("order", get_order_detail))
    dispatcher.add_handler(CommandHandler("balance", get_wallet_balance))
    dispatcher.add_handler(CommandHandler("reload", reload_wallet_balance))
    dispatcher.add_handler(CommandHandler("validate", validate_product))
    dispatcher.add_handler(CommandHandler("products", list_products_by_category))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()