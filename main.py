import os
import time
import hashlib
import requests
import unittest
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import asyncio

# Access environment variables
SMILE_EMAIL = "renedysanasam13@gmail.com"
SMILE_UID = "913332"
SMILE_KEY = "84d312c4e0799bac1d363c87be2e14b7"
TELEGRAM_TOKEN = "7796042656:AAH9WGYnmylnHFYY1uYro6K8cw6zh0hMJjo"
ADMIN_ID = "6501929376"  # Admin Telegram ID
UPI_ID = "9366673633@okbizaxis"

# API URLs
PRODUCT_API_URL = "https://www.smile.one/smilecoin/api/product"
PRODUCT_LIST_API_URL = "https://www.smile.one/smilecoin/api/productlist"
SERVER_LIST_API_URL = "https://www.smile.one/smilecoin/api/getserver"
ROLE_QUERY_API_URL = "https://www.smile.one/smilecoin/api/getrole"
CREATE_ORDER_API_URL = "https://www.smile.one/smilecoin/api/createorder"

# Function to generate the 'sign' parameter
def generate_sign(params, key):
    """
    Generate the 'sign' parameter by sorting fields, concatenating them, appending the key,
    and applying double MD5 hashing.

    :param params: Dictionary of parameters to be signed
    :param key: The encryption key (SMILE_KEY)
    :return: The generated 'sign' parameter
    """
    sorted_params = sorted(params.items())
    query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
    string_to_sign = f"{query_string}&{key}"
    return hashlib.md5(hashlib.md5(string_to_sign.encode()).hexdigest().encode()).hexdigest()

# Example of generating a real-time sign for Smile One API
def generate_real_time_sign():
    request_time = int(time.time())  # Current timestamp
    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "time": request_time,
    }
    sign = generate_sign(params, SMILE_KEY)
    return sign, request_time

# Example API request with real-time sign
def fetch_smile_one_balance():
    sign, request_time = generate_real_time_sign()
    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "time": request_time,
        "sign": sign,
    }

    response = requests.post(PRODUCT_API_URL, data=params)
    if response.status_code == 200:
        balance_data = response.json()
        balance = balance_data.get("balance", "N/A")  # Get the balance from the response
        print(f"Smile One Balance: ₹{balance}")
    else:
        print(f"Error fetching balance: {response.status_code}, {response.text}")

# In-memory product list
PRODUCT_LIST = []

# In-memory wallet for users
USER_WALLETS = {}

# In-memory reseller list
RESELLERS = set()

# Initialize the database
def init_db():
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            productid TEXT PRIMARY KEY,
            productname TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Ensure the database is initialized at the start of the program
init_db()

def update_db_schema():
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("""
        ALTER TABLE products ADD COLUMN reseller_price REAL DEFAULT 0.0
    """)
    conn.commit()
    conn.close()

# Call this function once to update the schema
# Uncomment the line below to run it
# update_db_schema()

def init_orders_table():
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            userid TEXT NOT NULL,
            zoneid TEXT NOT NULL,
            productname TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Call the function to initialize the orders table
init_orders_table()

def init_payments_table():
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid TEXT NOT NULL,
            amount REAL NOT NULL,
            reference TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Call the function to initialize the payments table
init_payments_table()

def remove_reseller_price_column():
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Rename the existing table
    cursor.execute("ALTER TABLE products RENAME TO products_old")

    # Create a new table without the `reseller_price` column
    cursor.execute("""
        CREATE TABLE products (
            productid TEXT PRIMARY KEY,
            productname TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Copy data from the old table to the new table
    cursor.execute("""
        INSERT INTO products (productid, productname, price)
        SELECT productid, productname, price FROM products_old
    """)

    # Drop the old table
    cursor.execute("DROP TABLE products_old")

    conn.commit()
    conn.close()

# Call this function once to remove the `reseller_price` column
# Uncomment the line below to execute it
# remove_reseller_price_column()

# Admin Commands
# Admin Command: Admin Panel with Buttons
async def admin_panel(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to access the Admin Panel.")
        return

    # Create buttons for admin commands
    keyboard = [
        [InlineKeyboardButton("Add Product", callback_data="addproduct")],
        [InlineKeyboardButton("Add Funds", callback_data="addfunds")],
        [InlineKeyboardButton("Update Product Price", callback_data="updateprice")],
        [InlineKeyboardButton("Change Product Details", callback_data="changeproduct")],
        [InlineKeyboardButton("Remove Product", callback_data="removeproduct")],
        [InlineKeyboardButton("View Product List", callback_data="viewproductlist")],
        [InlineKeyboardButton("Fetch Balance", callback_data="fetchbalance")],
        [InlineKeyboardButton("Server List", callback_data="serverlist")],
        [InlineKeyboardButton("View User Wallets", callback_data="viewusers")],  # New button
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Admin commands menu
    await update.message.reply_text("Admin Panel Commands:", reply_markup=reply_markup)

# Callback handler for admin buttons
async def admin_button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    # Handle button clicks based on callback_data
    if query.data == "addproduct":
        await query.edit_message_text("Use /addproduct <productid,productname,price>; <productid,productname,price>; ... to add products.")
    elif query.data == "addfunds":
        await query.edit_message_text("Use /addfunds <userid> <amount> to add funds to a user's wallet.")
    elif query.data == "updateprice":
        await query.edit_message_text("Use /updateprice <productid> <newprice> to update a product's price.")
    elif query.data == "changeproduct":
        await query.edit_message_text("Use /changeproduct <productid> <newname> <newprice> to change product details.")
    elif query.data == "removeproduct":
        await query.edit_message_text("Use /removeproduct <productid> to remove a product.")
    elif query.data == "viewproductlist":
        # Display the product list
        conn = sqlite3.connect("wallet.db")
        cursor = conn.cursor()
        cursor.execute("SELECT productid, productname, price FROM products")
        products = cursor.fetchall()
        conn.close()

        if not products:
            await query.edit_message_text("No products available.")
        else:
            product_message = "Product List:\n"
            for productid, productname, price in products:
                product_message += f"ID: {productid}: 💎 {productname}: ₹ {price}\n"
            await query.edit_message_text(product_message)
    elif query.data == "fetchbalance":
        # Fetch balance from Smile One
        request_time = int(time.time())
        params = {
            "email": SMILE_EMAIL,
            "uid": SMILE_UID,
            "time": request_time,
        }
        sign = generate_sign(params, SMILE_KEY)
        payload = {**params, "sign": sign}

        response = requests.post(PRODUCT_API_URL, data=payload)
        if response.status_code == 200:
            balance_data = response.json()
            balance = balance_data.get("balance", "N/A")  # Get the balance from the response
            await query.edit_message_text(f"Smile One Balance: ₹{balance}")
        else:
            await query.edit_message_text(f"Error fetching balance: {response.status_code}, {response.text}")
    elif query.data == "serverlist":
        await query.edit_message_text("Use /serverlist <userid> to get the server list for a user.")
    elif query.data == "viewusers":
        # Display user wallet balances
        if not USER_WALLETS:
            await query.edit_message_text("No users found.")
        else:
            user_message = "User Wallets:\n"
            for userid, balance in USER_WALLETS.items():
                user_message += f"User ID: {userid}, Balance: ₹{balance:.2f}\n"
            await query.edit_message_text(user_message)
    elif query.data == "manageresellers":
        await query.edit_message_text("Use /addreseller <userid> to add a reseller.\nUse /removereseller <userid> to remove a reseller.")

async def product_list_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: This command is for Admins only.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /productlist <userid>")
        return

    # Extract `userid` from the command arguments
    userid = context.args[0]
    product = "mobilelegends"
    request_time = int(time.time())

    # Prepare the parameters
    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "userid": userid,
        "product": product,
        "time": request_time,
    }
    sign = generate_sign(params, SMILE_KEY)
    payload = {**params, "sign": sign}

    # Make the API request
    response = requests.post(PRODUCT_LIST_API_URL, data=payload)
    if response.status_code == 200:
        await update.message.reply_text(f"Product List API Response: {response.json()}")
    else:
        await update.message.reply_text(f"Error: {response.status_code}, {response.text}")

async def server_list_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: This command is for Admins only.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /serverlist <userid>")
        return

    # Extract `userid` from the command arguments
    userid = context.args[0]
    product = "ragnarokm"
    request_time = int(time.time())

    # Prepare the parameters
    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "userid": userid,
        "product": product,
        "time": request_time,
    }
    sign = generate_sign(params, SMILE_KEY)
    payload = {**params, "sign": sign}

    # Make the API request
    response = requests.post(SERVER_LIST_API_URL, data=payload)
    if response.status_code == 200:
        await update.message.reply_text(f"Server List API Response: {response.json()}")
    else:
        await update.message.reply_text(f"Error: {response.status_code}, {response.text}")

# Admin Command: Add Product
async def add_product_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to add products.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /addproduct <productid,productname,price>; ...")
        return

    # Parse the input for multiple products
    products_input = " ".join(context.args)  # Combine all arguments into a single string
    products = products_input.split(";")  # Split by semicolon to get individual products

    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    added_products = []
    failed_products = []

    for product in products:
        product_details = product.strip().split(",")  # Split by comma to get product details
        if len(product_details) != 3:
            failed_products.append(f"Invalid format: {product.strip()}")
            continue

        productid, productname, price = product_details
        try:
            price = float(price)  # Convert price to float
            cursor.execute(
                "INSERT INTO products (productid, productname, price) VALUES (?, ?, ?)",
                (productid.strip(), productname.strip(), price)
            )
            conn.commit()
            added_products.append(f"ID: {productid.strip()}, 💎 {productname.strip()}, ₹ {price}")
        except sqlite3.IntegrityError:
            failed_products.append(f"Duplicate ID: {productid.strip()}")
        except ValueError:
            failed_products.append(f"Invalid price: {product.strip()}")

    conn.close()

    # Prepare the response message
    response_message = ""
    if added_products:
        response_message += "Products added successfully:\n" + "\n".join(added_products) + "\n"
    if failed_products:
        response_message += "Failed to add the following products:\n" + "\n".join(failed_products)

    await update.message.reply_text(response_message)

# Admin Command: Add Funds to User Wallet
async def add_funds_command(update: Update, context: CallbackContext) -> None:
    """
    Allows the admin to add funds to a user's wallet using their Telegram ID.
    """
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to add funds.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addfunds <telegram_id> <amount>")
        return

    # Extract `telegram_id` and `amount` from the command arguments
    telegram_id = context.args[0]
    try:
        amount = float(context.args[1])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except ValueError:
        await update.message.reply_text("Invalid amount. Please provide a valid number greater than zero.")
        return

    # Add funds to the user's wallet
    if telegram_id not in USER_WALLETS:
        USER_WALLETS[telegram_id] = 0.0
    USER_WALLETS[telegram_id] += amount

    # Notify the admin and the user
    await update.message.reply_text(f"Successfully added ₹{amount:.2f} to user {telegram_id}'s wallet. Current balance: ₹{USER_WALLETS[telegram_id]:.2f}")
    try:
        await context.bot.send_message(chat_id=telegram_id, text=f"₹{amount:.2f} has been added to your wallet by the admin. Current balance: ₹{USER_WALLETS[telegram_id]:.2f}")
    except Exception as e:
        await update.message.reply_text(f"Failed to notify the user: {e}")

# Admin Command: Update Product Price
async def update_product_price_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to update product prices.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /updateprice <productid> <newprice>")
        return

    # Extract product ID and new price
    productid = context.args[0]
    try:
        new_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid price. Please provide a valid number.")
        return

    # Update the product price in the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET price = ? WHERE productid = ?", (new_price, productid))
    if cursor.rowcount > 0:
        conn.commit()
        await update.message.reply_text(f"Product price updated successfully for ID: {productid}. New Price: ₹{new_price}")
    else:
        await update.message.reply_text(f"Product with ID {productid} not found.")
    conn.close()

# Admin Command: Remove Product
async def remove_product_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to remove products.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /removeproduct <productid>")
        return

    # Extract product ID
    productid = context.args[0]

    # Remove the product from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE productid = ?", (productid,))
    if cursor.rowcount > 0:
        conn.commit()
        await update.message.reply_text(f"Product with ID {productid} removed successfully.")
    else:
        await update.message.reply_text(f"Product with ID {productid} not found.")
    conn.close()

# Admin Command: Change Product Details
async def change_product_details_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to change product details.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /changeproduct <productid> <newname> <newprice>")
        return

    # Extract product ID, new name, and new price
    productid = context.args[0]
    new_name = context.args[1]
    try:
        new_price = float(context.args[2])
    except ValueError:
        await update.message.reply_text("Invalid price. Please provide a valid number.")
        return

    # Update the product details in the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET productname = ?, price = ? WHERE productid = ?", (new_name, new_price, productid))
    if cursor.rowcount > 0:
        conn.commit()
        await update.message.reply_text(f"Product details updated successfully for ID: {productid}. New Name: {new_name}, New Price: ₹{new_price}")
    else:
        await update.message.reply_text(f"Product with ID {productid} not found.")
    conn.close()

# Admin Command: Add Reseller
async def add_reseller_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to manage resellers.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /addreseller <userid>")
        return

    # Add the user to the reseller list
    reseller_id = context.args[0]
    RESELLERS.add(reseller_id)
    await update.message.reply_text(f"User {reseller_id} has been added as a reseller.")

# Admin Command: Remove Reseller
async def remove_reseller_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to manage resellers.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /removereseller <userid>")
        return

    # Remove the user from the reseller list
    reseller_id = context.args[0]
    if reseller_id in RESELLERS:
        RESELLERS.remove(reseller_id)
        await update.message.reply_text(f"User {reseller_id} has been removed from the reseller list.")
    else:
        await update.message.reply_text(f"User {reseller_id} is not a reseller.")

# Admin Command: View Pending Payments
async def view_payments_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to view payments.")
        return

    # Fetch pending payments from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT payment_id, userid, amount, reference, timestamp FROM payments WHERE status = 'PENDING'")
    payments = cursor.fetchall()
    conn.close()

    # Check if there are any pending payments
    if not payments:
        await update.message.reply_text("No pending payments.")
        return

    # Format the pending payments for display
    payment_message = "Pending Payments:\n"
    for payment_id, userid, amount, reference, timestamp in payments:
        payment_message += f"""
Payment ID: {payment_id}
User ID: {userid}
Amount: ₹{amount:.2f}
Reference: {reference}
Date: {timestamp}
---
"""
    await update.message.reply_text(payment_message)

# Admin Command: Verify Payment
async def verify_payment_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to verify payments.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /verifypayment <payment_id>")
        return

    # Extract `payment_id` from the command arguments
    try:
        payment_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid payment ID. Please provide a valid number.")
        return

    # Fetch the payment details from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT userid, amount FROM payments WHERE payment_id = ? AND status = 'PENDING'", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        await update.message.reply_text(f"Payment with ID {payment_id} not found or already verified.")
        conn.close()
        return

    userid, amount = payment

    # Add funds to the user's wallet
    if userid not in USER_WALLETS:
        USER_WALLETS[userid] = 0.0
    USER_WALLETS[userid] += amount

    # Update the payment status to "VERIFIED"
    cursor.execute("UPDATE payments SET status = 'VERIFIED' WHERE payment_id = ?", (payment_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Payment with ID {payment_id} verified successfully! ₹{amount:.2f} added to user {userid}'s wallet.")

# Admin Command: Reject Payment
async def reject_payment_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to reject payments.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /rejectpayment <payment_id>")
        return

    # Extract `payment_id` from the command arguments
    try:
        payment_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid payment ID. Please provide a valid number.")
        return

    # Fetch the payment details from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT userid, amount FROM payments WHERE payment_id = ? AND status = 'PENDING'", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        await update.message.reply_text(f"Payment with ID {payment_id} not found or already processed.")
        conn.close()
        return

    userid, amount = payment

    # Update the payment status to "REJECTED"
    cursor.execute("UPDATE payments SET status = 'REJECTED' WHERE payment_id = ?", (payment_id,))
    conn.commit()
    conn.close()

    # Notify the admin and the user
    await update.message.reply_text(f"Payment with ID {payment_id} has been rejected.")
    try:
        await context.bot.send_message(chat_id=userid, text=f"Your payment of ₹{amount:.2f} with ID {payment_id} has been rejected by the admin.")
    except Exception as e:
        await update.message.reply_text(f"Failed to notify the user: {e}")

# Admin Command: Manage Product Categories
async def manage_product_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to manage products.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /manageproduct <productid> <category>\nCategories: diamond, doublediamond, wkp")
        return

    # Extract product ID and category
    productid = context.args[0]
    category = context.args[1].lower()

    # Validate the category
    valid_categories = ["diamond", "doublediamond", "wkp"]
    if category not in valid_categories:
        await update.message.reply_text(f"Invalid category. Valid categories are: {', '.join(valid_categories)}")
        return

    # Update the product category in the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET productname = productname || ' [%s]' WHERE productid = ?" % category.capitalize(), (productid,))
    if cursor.rowcount > 0:
        conn.commit()
        await update.message.reply_text(f"Product with ID {productid} has been categorized as {category.capitalize()}.")
    else:
        await update.message.reply_text(f"Product with ID {productid} not found.")
    conn.close()

# Admin Command: Bulk Manage Product Categories
async def manage_product_command(update: Update, context: CallbackContext) -> None:
    # Check if the user is the admin
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("Access Denied: You are not authorized to manage products.")
        return

    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /manageproduct <productid1,category1;productid2,category2;...>\n"
            "Categories: diamond, bonus, wkp"
        )
        return

    # Parse the input for multiple products
    products_input = " ".join(context.args)  # Combine all arguments into a single string
    products = products_input.split(";")  # Split by semicolon to get individual product-category pairs

    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    updated_products = []
    failed_products = []

    for product in products:
        product_details = product.strip().split(",")  # Split by comma to get product ID and category
        if len(product_details) != 2:
            failed_products.append(f"Invalid format: {product.strip()}")
            continue

        productid, category = product_details
        category = category.lower()

        # Validate the category
        valid_categories = ["diamond", "bonus", "wkp"]
        if category not in valid_categories:
            failed_products.append(f"Invalid category: {product.strip()}")
            continue

        # Check if the product exists in the database
        cursor.execute("SELECT * FROM products WHERE productid = ?", (productid.strip(),))
        if not cursor.fetchone():
            failed_products.append(f"Product not found: {product.strip()}")
            continue

        # Update the product category in the database
        cursor.execute(
            "UPDATE products SET productname = productname || ' [%s]' WHERE productid = ?" % category.capitalize(),
            (productid.strip(),)
        )
        if cursor.rowcount > 0:
            conn.commit()
            updated_products.append(f"Product ID: {productid.strip()} categorized as {category.capitalize()}")
        else:
            failed_products.append(f"Failed to update: {product.strip()}")

    conn.close()

    # Prepare the response message
    response_message = ""
    if updated_products:
        response_message += "Products updated successfully:\n" + "\n".join(updated_products) + "\n"
    if failed_products:
        response_message += "Failed to update the following products:\n" + "\n".join(failed_products)

    await update.message.reply_text(response_message)

# User Commands
async def user_panel(update: Update, context: CallbackContext) -> None:
    commands = """
User Panel Commands:
/rolequery <userid> <zoneid> <productid> - Query role information
/purchase <userid> <zoneid> <productid> - Create an order
/showproducts - Show available products
"""
    await update.message.reply_text(commands)

async def role_query_command(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /rolequery <userid> <zoneid> <productid>")
        return

    userid = context.args[0]
    zoneid = context.args[1]
    productid = context.args[2]
    product = "mobilelegends"
    request_time = int(time.time())

    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "userid": userid,
        "zoneid": zoneid,
        "product": product,
        "productid": productid,
        "time": request_time,
    }
    sign = generate_sign(params, SMILE_KEY)
    payload = {**params, "sign": sign}

    response = requests.post(ROLE_QUERY_API_URL, data=payload)
    if response.status_code == 200:
        await update.message.reply_text(f"Role Query API Response: {response.json()}")
    else:
        await update.message.reply_text(f"Error: {response.status_code}, {response.text}")

async def purchase_command(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /purchase <userid> <zoneid> <productid>")
        return

    userid = context.args[0]
    zoneid = context.args[1]
    productid = context.args[2]
    product = "mobilelegends"
    request_time = int(time.time())

    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "userid": userid,
        "zoneid": zoneid,
        "product": product,
        "productid": productid,
        "time": request_time,
    }
    sign = generate_sign(params, SMILE_KEY)
    payload = {**params, "sign": sign}

    response = requests.post(CREATE_ORDER_API_URL, data=payload)
    if response.status_code == 200:
        await update.message.reply_text(f"Purchase API Response: {response.json()}")
    else:
        await update.message.reply_text(f"Error: {response.status_code}, {response.text}")

async def ml_command(update: Update, context: CallbackContext) -> None:
    # Check if the required arguments are provided
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /ml <userid> <zoneid> <productname>")
        return

    # Extract `userid`, `zoneid`, and `productname` from the command arguments
    userid = context.args[0]
    zoneid = context.args[1]
    productname = " ".join(context.args[2:])  # Handle multi-word product names

    # Find the product ID and price based on the product name
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT productid, price FROM products WHERE productname = ?", (productname,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        await update.message.reply_text(f"Product '{productname}' not found. Please check the available products using /showproducts.")
        return

    productid, price = product

    # Check if the user has enough funds
    if userid not in USER_WALLETS or USER_WALLETS[userid] < price:
        await update.message.reply_text(f"Insufficient funds. Please ask the admin to add funds to your wallet.")
        return

    # Fetch Smile One balance
    request_time = int(time.time())
    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "time": request_time,
    }
    sign = generate_sign(params, SMILE_KEY)
    payload = {**params, "sign": sign}

    response = requests.post(PRODUCT_API_URL, data=payload)
    if response.status_code == 200:
        balance_data = response.json()
        smile_balance = float(balance_data.get("balance", 0))  # Get the balance from the response

        # Check if Smile One balance is sufficient
        if smile_balance < price:
            await update.message.reply_text("OUT OF STOCK")
            return
    else:
        await update.message.reply_text(f"Error fetching Smile One balance: {response.status_code}, {response.text}")
        return

    # Deduct the price from the user's wallet
    USER_WALLETS[userid] -= price

    # Prepare the parameters for the API request
    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "userid": userid,
        "zoneid": zoneid,
        "product": "mobilelegends",  # Example product type
        "productid": productid,
        "time": request_time,
    }
    sign = generate_sign(params, SMILE_KEY)
    payload = {**params, "sign": sign}

    # Make the API request to create an order
    response = requests.post(CREATE_ORDER_API_URL, data=payload)
    if response.status_code == 200:
        response_data = response.json()
        order_id = response_data.get("order_id", "N/A")  # Get the order ID from the response
        username = update.effective_user.username or update.effective_user.first_name or "User"

        # Save the order details to the database
        conn = sqlite3.connect("wallet.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (order_id, userid, zoneid, productname, price, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, userid, zoneid, productname, price, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        # Transaction report message
        transaction_report = f"""
===Transaction Report===
Order Status: SUCCESSFUL✅
Order ID: {order_id}
User Name: {username}
Game ID: {userid}
Game Server: {zoneid}
Items: {productname}
Total Amount: ₹{price:.2f}
"""
        await update.message.reply_text(transaction_report)
    else:
        # Refund the amount if the order fails
        USER_WALLETS[userid] += price
        await update.message.reply_text(f"Error: {response.status_code}, {response.text}. Refunded ₹{price:.2f} to your wallet.")

# User Command: Show Products
async def show_products_command(update: Update, context: CallbackContext) -> None:
    # Message to display additional commands
    product_categories_message = """
Available Product Categories:
/diamond - Show Diamonds
/doublediamond - Show Double Diamonds
/wkp - Show Weekly Pass
"""
    await update.message.reply_text(product_categories_message)

# User Command: Check Wallet Balance
async def wallet_command(update: Update, context: CallbackContext) -> None:
    # Get the user's ID
    userid = str(update.effective_user.id)

    # Check the user's wallet balance
    balance = USER_WALLETS.get(userid, 0.0)
    await update.message.reply_text(f"Your wallet balance is: {balance:.2f}")

# User Command: Buy Funds
async def buy_command(update: Update, context: CallbackContext) -> None:
    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /buy <amount>")
        return

    # Extract the amount from the command arguments
    try:
        amount = float(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except ValueError:
        await update.message.reply_text("Invalid amount. Please provide a valid number greater than zero.")
        return

    # Generate a random reference number
    reference_number = f"REF-{random.randint(100000, 999999)}"
    user_id = str(update.effective_user.id)

    # Save the payment details to the database with a "PENDING" status
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payments (userid, amount, reference, status, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, reference_number, "PENDING", time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    # Notify the user
    buy_message = f"""
💳 Add Funds to Your Wallet

Amount: ₹{amount:.2f}
📝 Payment Reference: {reference_number}
"""
    await update.message.reply_text(buy_message, parse_mode="Markdown")

async def start(update: Update, context: CallbackContext) -> None:
    # Get the user's information
    user = update.effective_user
    username = user.username if user.username else user.first_name if user.first_name else "User"

    # Welcome message
    welcome_message = f"""
🚀 Welcome to {username}!

💎 MLBB Diamond Store
- Instant Delivery
- Best Prices
- 24/7 Support

Available Commands:
/showproducts - Show available products
/wallet - Check your wallet balance
/buy <amount> - Add funds to your wallet
/ml <userid> <zoneid> <productname> - Purchase a product
"""
    await update.message.reply_text(welcome_message)

# User Command: Show Diamonds
async def show_diamonds_command(update: Update, context: CallbackContext) -> None:
    # Fetch diamonds from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT productname, price FROM products WHERE productname LIKE '%[Diamond]%'")
    products = cursor.fetchall()
    conn.close()

    # Check if there are any diamond products
    if not products:
        await update.message.reply_text("No diamond products available at the moment.")
        return

    # Format the diamond product list for display
    product_message = "Available Diamonds:\n"
    for productname, price in products:
        product_message += f"💎 {productname.replace(' [Diamond]', '')}: ₹ {price}\n"

    await update.message.reply_text(product_message)

# User Command: Show Double Diamonds
async def show_double_diamonds_command(update: Update, context: CallbackContext) -> None:
    # Fetch double diamonds from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT productname, price FROM products WHERE productname LIKE '%[Double Diamond]%'")
    products = cursor.fetchall()
    conn.close()

    # Check if there are any double diamond products
    if not products:
        await update.message.reply_text("No double diamond products available at the moment.")
        return

    # Format the double diamond product list for display
    product_message = "Available Double Diamonds:\n"
    for productname, price in products:
        product_message += f"💎 {productname.replace(' [Double Diamond]', '')}: ₹ {price}\n"

    await update.message.reply_text(product_message)

# User Command: Show Weekly Pass
async def show_weekly_pass_command(update: Update, context: CallbackContext) -> None:
    # Fetch weekly pass products from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT productname, price FROM products WHERE productname LIKE '%[Wkp]%'")
    products = cursor.fetchall()
    conn.close()

    # Check if there are any weekly pass products
    if not products:
        await update.message.reply_text("No weekly pass products available at the moment.")
        return

    # Format the weekly pass product list for display
    product_message = "Available Weekly Passes:\n"
    for productname, price in products:
        product_message += f"💎 {productname.replace(' [Wkp]', '')}: ₹ {price}\n"

    await update.message.reply_text(product_message)

# User Command: Show Bonus Products
async def show_bonus_command(update: Update, context: CallbackContext) -> None:
    # Fetch bonus products from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT productname, price FROM products WHERE productname LIKE '%[Bonus]%'")
    products = cursor.fetchall()
    conn.close()

    # Check if there are any bonus products
    if not products:
        await update.message.reply_text("No bonus products available at the moment.")
        return

    # Format the bonus product list for display
    product_message = "Available Bonus Products:\n"
    for productname, price in products:
        product_message += f"💎 {productname.replace(' [Bonus]', '')}: ₹ {price}\n"

    await update.message.reply_text(product_message)

async def get_id_command(update: Update, context: CallbackContext) -> None:
    """
    Responds with the user's Telegram ID.
    """
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your Telegram ID is: {user_id}")

async def get_role_command(update: Update, context: CallbackContext) -> None:
    """
    Responds with a placeholder message for the user's role.
    """
    user_id = update.effective_user.id
    await update.message.reply_text(f"User ID {user_id}: Role functionality is not implemented yet.")

async def order_history_command(update: Update, context: CallbackContext) -> None:
    """
    Displays the user's order history.
    """
    user_id = str(update.effective_user.id)

    # Fetch the user's order history from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, productname, price, timestamp
        FROM orders
        WHERE userid = ?
        ORDER BY timestamp DESC
    """, (user_id,))
    orders = cursor.fetchall()
    conn.close()

    # Check if there are any orders
    if not orders:
        await update.message.reply_text("You have no order history.")
        return

    # Format the order history for display
    order_message = "Your Order History:\n"
    for order_id, productname, price, timestamp in orders:
        order_message += f"""
Order ID: {order_id}
Product: {productname}
Price: ₹{price:.2f}
Date: {timestamp}
---
"""
    await update.message.reply_text(order_message)

# Main function to start the bot
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(admin_button_handler))
    application.add_handler(CommandHandler("productlist", product_list_command))
    application.add_handler(CommandHandler("serverlist", server_list_command))
    application.add_handler(CommandHandler("addproduct", add_product_command))
    application.add_handler(CommandHandler("addfunds", add_funds_command))
    application.add_handler(CommandHandler("updateprice", update_product_price_command))
    application.add_handler(CommandHandler("changeproduct", change_product_details_command))
    application.add_handler(CommandHandler("removeproduct", remove_product_command))
    application.add_handler(CommandHandler("user", user_panel))
    application.add_handler(CommandHandler("rolequery", role_query_command))
    application.add_handler(CommandHandler("purchase", purchase_command))
    application.add_handler(CommandHandler("ml", ml_command))
    application.add_handler(CommandHandler("showproducts", show_products_command))
    application.add_handler(CommandHandler("wallet", wallet_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("getid", get_id_command))
    application.add_handler(CommandHandler("orderhistory", order_history_command))
    application.add_handler(CommandHandler("viewpayments", view_payments_command))
    application.add_handler(CommandHandler("verifypayment", verify_payment_command))
    application.add_handler(CommandHandler("rejectpayment", reject_payment_command))
    application.add_handler(CallbackQueryHandler(admin_button_handler))
    application.add_handler(CommandHandler("diamond", show_diamonds_command))
    application.add_handler(CommandHandler("wkp", show_weekly_pass_command))
    application.add_handler(CommandHandler("manageproduct", manage_product_command))
    application.add_handler(CommandHandler("bonus", show_bonus_command))

    # Start the bot
    try:
        application.run_polling()
    except telegram.error.Conflict:
        print("Conflict: terminated by other getUpdates request; make sure that only one bot instance is running")

# Unit tests
class TestSmileOneAPI(unittest.TestCase):

    def test_generate_sign(self):
        params = {
            "time": 1744825223,
        }
        key = "84d312c4e0799bac1d363c87be2e14b7"
        expected_sign = "cc027bb14f8d0a4cdc60ca149a324290"  # Replace with the correct expected value
        generated_sign = generate_sign(params, key)
        self.assertEqual(generated_sign, expected_sign)

if __name__ == "__main__":
    main()
    # Run unit tests
    unittest.main()