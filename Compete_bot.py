from dotenv import load_dotenv
import os
import time
import hashlib
import requests
from requests.exceptions import ConnectionError, Timeout
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from datetime import datetime, timedelta
import sqlite3
import cloudscraper

#Telegram bot token
TELEGRAM_BOT_TOKEN = "7796042656:AAH9WGYnmylnHFYY1uYro6K8cw6zh0hMJjo"
BOT_NAME = "KendyTopupBot"
ADMIN_USER_NAME = "@kendyenterprises"
ADMIN_ID = "6501929376"  # Replace with the actual admin Telegram ID

# Load environment variables
SMILE_EMAIL = "renedysanasam13@gmail.com"
SMILE_UID = "913332"
SMILE_KEY = "84d312c4e0799bac1d363c87be2e14b7"
# Base API URL
BASE_API_URL = "https://www.smile.one"

# Define the API URL for creating orders
CREATE_ORDER_API_URL = f"{BASE_API_URL}/smilecoin/api/createorder"

# BharatPe API credentials
UPI_ID = "BHARATPE09911990897@yesbankltd"
BHARATPE_MERCHANT_ID = "39271741"
BHARATPE_TOKEN = "caa0fde42822418da23f4d0a7fd4daa9"
BHARATPE_API_URL = "https://payments-tesseract.bharatpe.in/api/v1/merchant/transactions"

# Function to generate the 'sign' parameter
def generate_sign(params, key):
    sorted_params = sorted(params.items())
    query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
    string_to_sign = f"{query_string}&{key}"
    return hashlib.md5(hashlib.md5(string_to_sign.encode()).hexdigest().encode()).hexdigest()

# Function to get the country-specific API URL
def get_country_specific_url(base_url, country_code):
    """
    Append the country code to the base URL.
    :param base_url: The base API URL
    :param country_code: The country code (e.g., 'br', 'ru', 'ph')
    :return: The country-specific API URL
    """
    return f"{base_url}/{country_code}"

# Function to query points
def query_points(uid, email, product, key):
    api_url = f"{BASE_API_URL}/smilecoin/api/querypoints"
    request_time = int(time.time())
    params = {"uid": uid, "email": email, "product": product, "time": request_time}
    params["sign"] = generate_sign(params, key)
    response = requests.post(api_url, data=params)
    print("Request Params:", params)
    print("Response:", response.json())
    return response.json() if response.status_code == 200 else {"error": response.text}

# Function to get product details
def get_product(uid, email, product, key):
    api_url = f"{BASE_API_URL}/smilecoin/api/product"
    request_time = int(time.time())
    params = {"uid": uid, "email": email, "product": product, "time": request_time}
    params["sign"] = generate_sign(params, key)
    response = requests.post(api_url, data=params)
    print("Request Params:", params)
    print("Response:", response.json())
    return response.json() if response.status_code == 200 else {"error": response.text}

# Function to get the product list
def get_product_list(uid, email, product, key):
    api_url = f"{BASE_API_URL}/smilecoin/api/productlist"
    request_time = int(time.time())
    params = {"uid": uid, "email": email, "product": product, "time": request_time}
    params["sign"] = generate_sign(params, key)
    response = requests.post(api_url, data=params)
    print("Request Params:", params)
    print("Response:", response.json())
    return response.json() if response.status_code == 200 else {"error": response.text}

# Function to get the server list
def get_server_list(email, uid, product, key):
    api_url = f"{BASE_API_URL}/smilecoin/api/getserver"
    request_time = int(time.time())
    params = {"email": email, "uid": uid, "product": product, "time": request_time}
    params["sign"] = generate_sign(params, key)
    response = requests.post(api_url, data=params)
    print("Request Params:", params)
    print("Response:", response.json())
    return response.json() if response.status_code == 200 else {"error": response.text}

# Function to query roles
def query_role(email, uid, userid, zoneid, product, productid, key):
    api_url = f"{BASE_API_URL}/smilecoin/api/getrole"
    request_time = int(time.time())
    params = {
        "email": email,
        "uid": uid,
        "userid": userid,
        "zoneid": zoneid,
        "product": product,
        "productid": productid,
        "time": request_time,
    }
    params["sign"] = generate_sign(params, key)
    response = requests.post(api_url, data=params)
    print("Request Params:", params)
    print("Response:", response.json())
    return response.json() if response.status_code == 200 else {"error": response.text}

# Function to create an order
def create_order(email, uid, userid, zoneid, product, productid, key):
    api_url = f"{BASE_API_URL}/smilecoin/api/createorder"
    request_time = int(time.time())
    params = {
        "email": email,
        "uid": uid,
        "userid": userid,
        "zoneid": zoneid,
        "product": product,
        "productid": productid,
        "time": request_time,
    }
    params["sign"] = generate_sign(params, key)

    # Use cloudscraper to bypass Cloudflare protection
    scraper = cloudscraper.create_scraper()
    response = scraper.post(api_url, data=params)

    print("Request Params:", params)

    try:
        # Attempt to parse the response as JSON
        response_data = response.json()
        print("Response:", response_data)
        return response_data
    except Exception as e:
        # Handle non-JSON responses
        print("Response (non-JSON):", response.text)
        truncated_response = response.text[:500]  # Truncate the response to 500 characters
        return {"error": f"Invalid response from API: {truncated_response}"}

def initialize_database():
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Create the users table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            email TEXT NOT NULL,
            key TEXT NOT NULL,
            balance NUMBER NOT NULL DEFAULT 0,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create the orders table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid TEXT NOT NULL,
            zoneid TEXT NOT NULL,
            product TEXT NOT NULL,
            productid TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create the products table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            productname TEXT NOT NULL,
            productid TEXT NOT NULL,
            price NUMBER NOT NULL,
            category TEXT NOT NULL,
            createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create the payments table if it does not exist
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
    print("Database initialized successfully.")

# Function to update the database schema
def update_database_schema():
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Add the telegram_id column to the orders table if it doesn't exist
    try:
        cursor.execute("""
            ALTER TABLE orders ADD COLUMN telegram_id TEXT
        """)
        print("telegram_id column added to orders table.")
    except sqlite3.OperationalError:
        print("telegram_id column already exists in orders table.")

    conn.commit()
    conn.close()
    print("Database schema updated successfully.")

# Function to check if the user is registered
def is_user_registered(user_id):
    """
    Check if the user is registered in the database.
    :param user_id: Telegram user ID
    :return: True if the user is registered, False otherwise
    """
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE uid = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# Function to handle the /start command
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    chat_id = update.effective_chat.id

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Check if the user is already registered
    cursor.execute("SELECT id FROM users WHERE uid = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        # Register the user if not already registered
        cursor.execute(
            "INSERT INTO users (uid, email, key, balance) VALUES (?, ?, ?, ?)",
            (user_id, f"{username}@example.com", "default_key", 0),  # Default balance
        )
        conn.commit()

    # Fetch user balance
    cursor.execute("SELECT balance FROM users WHERE uid = ?", (user_id,))
    balance = cursor.fetchone()[0]

    # Welcome message
    welcome_message = f"""
🚀 Welcome {username} to Kendy Top-up Bot!
-------------------------------
🆔 Your Telegram ID: {user_id}
💰 Your Current Balance: ₹{balance:.2f}
-------------------------------
- Instant Delivery
- Best Prices
- Secure Payments
- Easy to Use
- Fast Transactions
- 24/7 Support
-------------------------------
✅ User commands: 
-----------------------
📢 Check products:
 /large_pack - Show available Large pack Diamonds
 /small_pack - Show available Small pack Diamonds
 /wkp - Show available Weekly Passes
 /bonus - Show available Bonus Products
------------------------
📢 Add fund & verified Commands:
 /wallet - Check your wallet balance
 /utr <utr_number> - Verify your UPI transaction

Payment Methods: {UPI_ID}\nCopy the UPI ID and pay to it. After payment, use the /utr command to verify your transaction.
------------------------
📢 Order Commands
/br <ml_id> <server_id> <product_name> - Large pack Diamonds, Weekly Passes & Bonus Products
/ph <ml_id> <server_id> <product_name> - Small pack Diamonds
------------------------
❓ /help to see all commands
------------------------

⚠️ Note: Do not share your UPI transaction UTR number with anyone.
If you have any questions, feel free to ask!
"""
    # Send the welcome message
    await context.bot.send_message(chat_id=chat_id, text=welcome_message)

    # Close the database connection
    conn.close()

# Function to handle the /wallet command
async def wallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the user is registered
    if not is_user_registered(user_id):
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not registered. Please use /start to register.")
        return

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Fetch the user's balance
    cursor.execute("SELECT balance FROM users WHERE uid = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        balance = user[0]
        wallet_message = f"💰 Your Current Wallet Balance: ₹{balance:.2f}"
    else:
        wallet_message = "❌ Unable to fetch your balance. Please try again later."

    # Send the wallet balance message
    await context.bot.send_message(chat_id=chat_id, text=wallet_message)

    # Close the database connection
    conn.close()

# Function to handle the /user command (Admin Panel)
async def user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the user is the admin
    if str(user_id) != ADMIN_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this command.")
        return

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Fetch all users and their details
    cursor.execute("""
        SELECT u.uid, u.email, u.balance, 
               (SELECT COUNT(*) FROM orders WHERE orders.userid = u.uid) AS total_orders,
               u.role, u.created_at
        FROM users u
    """)
    users = cursor.fetchall()

    if users:
        user_list = "👥 Registered Users:\n\n"
        for user in users:
            user_list += f"""
Telegram ID: {user[0]}
Username: {user[1]}
Balance: ₹{user[2]:.2f}
Total Orders: {user[3]}
Register Date: {user[5]}
Role: {user[4]}
-------------------------------
"""
    else:
        user_list = "❌ No users found in the database."

    # Send the user list to the admin
    await context.bot.send_message(chat_id=chat_id, text=user_list)

    # Close the database connection
    conn.close()

# Function to handle the /order command
async def order_command(update: Update, context: CallbackContext) -> None:
    # Check if the required arguments are provided
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /order <userid> <zoneid> <productname>")
        return

    # Extract arguments
    userid = context.args[0]
    zoneid = context.args[1]
    productname = " ".join(context.args[2:])  # Handle multi-word product names
    telegram_id = str(update.effective_user.id)  # Get the Telegram ID of the user

    # Fetch the product details from the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT productid, price FROM products WHERE productname = ?", (productname,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        await update.message.reply_text(f"Product '{productname}' not found. Please check the available products.")
        return

    productid, price = product

    # Check if the user has enough funds
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE uid = ?", (telegram_id,))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data or user_data[0] < price:
        await update.message.reply_text(f"Insufficient funds. Please add funds to your wallet using /buy <amount>.")
        return

    # Deduct the price from the user's wallet
    new_balance = user_data[0] - price
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE uid = ?", (new_balance, telegram_id))
    conn.commit()
    conn.close()

    # Prepare the parameters for the API request
    request_time = int(time.time())
    params = {
        "email": SMILE_EMAIL,
        "uid": SMILE_UID,
        "userid": userid,
        "zoneid": zoneid,
        "product": "mobilelegends",
        "productid": productid,
        "time": request_time,
    }
    sign = generate_sign(params, SMILE_KEY)
    payload = {**params, "sign": sign}

    # Make the API request to create an order
    response = requests.post(CREATE_ORDER_API_URL, data=payload)
    if response.status_code == 200:
        response_data = response.json()

        # Save the order details to the database
        order_id = response_data.get("order_id", "Unknown")
        conn = sqlite3.connect("wallet.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (userid, zoneid, product, productid, telegram_id, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (userid, zoneid, productname, productid, telegram_id))
        conn.commit()
        conn.close()

        # Transaction report message
        transaction_report = f"""
✅ Transaction Successful!
Order ID: {order_id}
User ID: {userid}
Server ID: {zoneid}
Product: {productname}
Price: ₹{price:.2f}
Current Balance: ₹{new_balance:.2f}
"""
        await update.message.reply_text(transaction_report)
    else:
        # Refund the amount if the order fails
        conn = sqlite3.connect("wallet.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE uid = ?", (price, telegram_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"Error: {response.status_code}, {response.text}. Refunded ₹{price:.2f} to your wallet.")

# Function to handle the /his command
async def order_history(update: Update, context: CallbackContext):
    telegram_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Fetch the user's order history
    cursor.execute("""
        SELECT product, productid, zoneid, created_at
        FROM orders
        WHERE telegram_id = ?
        ORDER BY created_at DESC
    """, (telegram_id,))
    orders = cursor.fetchall()

    # Check if there are any orders
    if not orders:
        await context.bot.send_message(chat_id=chat_id, text="❌ You have no order history.")
        conn.close()
        return

    # Format the order history for display
    order_message = "📜 Your Order History:\n\n"
    for order in orders:
        product, productid, zoneid, created_at = order
        order_message += f"""
🛒 Product: {product}
🔑 Product ID: {productid}
🌐 Zone ID: {zoneid}
📅 Date: {created_at}
-------------------------------
"""

    # Send the order history to the user
    await context.bot.send_message(chat_id=chat_id, text=order_message)

    # Close the database connection
    conn.close()

# Helper function to fetch product price from the database
def get_product_price(product_name):
    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Fetch the product price based on the product name
    cursor.execute("SELECT price FROM products WHERE product_name = ?", (product_name,))
    product = cursor.fetchone()

    # Close the database connection
    conn.close()

    # Return the price if the product is found, otherwise return None
    return float(product[0]) if product else None

# Function to handle the /product_management command (Admin Panel)
async def product_management(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the user is the admin
    if str(user_id) != ADMIN_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this command.")
        return

    # Ensure the admin provided product details
    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid command format. Use:\n/product_management <product_id>:<category>,<product_id>:<category>")
        return

    # Parse the product details
    product_details = " ".join(context.args)
    products = product_details.split(",")

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Assign categories to products
    for product in products:
        try:
            product_id, category = product.split(":")
            cursor.execute("""
                UPDATE products
                SET category = ?
                WHERE product_id = ?
            """, (category.strip().lower(), product_id.strip()))
        except ValueError:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Invalid format: {product}. Skipping...")
            continue

    conn.commit()
    conn.close()

    # Send success message
    await context.bot.send_message(chat_id=chat_id, text="✅ Product categories updated successfully!")

# Function to handle the /addproduct command (Admin Panel)
async def add_product(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the user is the admin
    if str(user_id) != ADMIN_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this command.")
        return

    # Ensure the admin provided product details
    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid command format. Use:\n/addproduct <productname>:<productid>:<price>:<category>,<productname>:<productid>:<price>:<category>")
        return

    # Parse the product details
    product_details = " ".join(context.args)
    products = product_details.split(",")

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Add each product to the database
    for product in products:
        try:
            productname, productid, price, category = product.split(":")
            cursor.execute("""
                INSERT INTO products (productname, productid, price, category, createdat)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (productname.strip(), productid.strip(), float(price.strip()), category.strip().lower()))
        except ValueError:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Invalid product format: {product}. Skipping...")
            continue

    conn.commit()
    conn.close()

    # Send success message
    await context.bot.send_message(chat_id=chat_id, text="✅ Products added successfully!")

# Function to show products by category
async def show_products(update: Update, context: CallbackContext, category: str):
    chat_id = update.effective_chat.id

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Fetch products in the specified category
    cursor.execute("SELECT productname, price FROM products WHERE category = ?", (category,))
    products = cursor.fetchall()

    if products:
        product_list = f"💎 {category.capitalize()} Category\n-----------------\n"
        for product in products:
            product_list += f"{product[0]} 💎: ₹{float(product[1]):.2f}\n"
    else:
        product_list = f"❌ No products found in the {category.capitalize()} category."

    # Send the product list to the user
    await context.bot.send_message(chat_id=chat_id, text=product_list)

    # Close the database connection
    conn.close()

# Command handlers for each category
async def small_pack(update: Update, context: CallbackContext):
    await show_products(update, context, "small_pack")

async def large_pack(update: Update, context: CallbackContext):
    await show_products(update, context, "large_pack")

async def wkp(update: Update, context: CallbackContext):
    await show_products(update, context, "wkp")

async def bonus(update: Update, context: CallbackContext):
    await show_products(update, context, "bonus")
    

# Run the database initialization and schema update
initialize_database()
update_database_schema()

# Function to handle the /getid command
async def getid(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    chat_id = update.effective_chat.id

    # Send the user's Telegram ID
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🆔 Your Telegram ID: {user_id}\n👤 Username: {username}"
    )
# Function to fetch the product list for a specific country
async def fetch_product_list(update: Update, context: CallbackContext, country_code: str) -> None:
    api_url = f"{BASE_API_URL}/{country_code}/smilecoin/api/productlist"
    request_time = int(time.time())
    params = {
        "uid": SMILE_UID,
        "email": SMILE_EMAIL,
        "product": "mobilelegends",
        "time": request_time,
    }
    params["sign"] = generate_sign(params, SMILE_KEY)

    response = fetch_with_retry(api_url, params)
    if response is None:
        await update.message.reply_text(f"❌ Unable to fetch product list for {country_code.upper()}.")
        return

    product_list = response.json().get("data", {}).get("product", [])
    if not product_list:
        await update.message.reply_text(f"No products found for {country_code.upper()}.")
        return

    product_message = f"Product List for {country_code.upper()}:\n"
    for product in product_list:
        product_message += f"ID: {product['id']},- {product['spu']},-💲{product['price']}\n"
    await update.message.reply_text(product_message)

# Function to check if the user is an admin
def is_admin(user_id: str) -> bool:
    return str(user_id) == ADMIN_ID

# Command handler for /fatchbr (restricted to admin)
async def fetch_br_products(update: Update, context: CallbackContext) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    await fetch_product_list(update, context, "br")

# Command handler for /fatchph (restricted to admin)
async def fetch_ph_products(update: Update, context: CallbackContext) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    await fetch_product_list(update, context, "ph")
def fetch_with_retry(api_url, params, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.post(api_url, data=params)
            if response.status_code == 200:
                return response
        except ConnectionError:
            print(f"Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
    return None

async def fetch_product_list(update: Update, context: CallbackContext, country_code: str) -> None:
    api_url = f"{BASE_API_URL}/{country_code}/smilecoin/api/productlist"
    request_time = int(time.time())
    params = {
        "uid": SMILE_UID,
        "email": SMILE_EMAIL,
        "product": "mobilelegends",
        "time": request_time,
    }
    params["sign"] = generate_sign(params, SMILE_KEY)

    response = fetch_with_retry(api_url, params)
    if response is None:
        await update.message.reply_text(f"❌ Unable to fetch product list for {country_code.upper()}.")
        return

    product_list = response.json().get("data", {}).get("product", [])
    if not product_list:
        await update.message.reply_text(f"No products found for {country_code.upper()}.")
        return


    product_message = f"Product List for {country_code.upper()}:\n"
    for product in product_list:
        product_message += f"ID: {product['id']},- {product['spu']},-💲{product['price']}\n"
    await update.message.reply_text(product_message)

# Function to handle the /addfund command (Admin Only)
async def add_fund(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the user is the admin
    if str(user_id) != ADMIN_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this command.")
        return

    # Ensure the admin provided the required arguments
    if len(context.args) < 2:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid command format. Use:\n/addfund <telegram_id> <amount>")
        return

    # Extract the arguments
    target_telegram_id = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid amount. Please provide a valid number.")
        return

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Check if the target user exists
    cursor.execute("SELECT balance FROM users WHERE uid = ?", (target_telegram_id,))
    user = cursor.fetchone()

    if not user:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ User with Telegram ID {target_telegram_id} not found.")
        conn.close()
        return

    # Update the user's balance
    new_balance = user[0] + amount
    cursor.execute("UPDATE users SET balance = ? WHERE uid = ?", (new_balance, target_telegram_id))
    conn.commit()
    conn.close()

    # Send a success message
    await context.bot.send_message(chat_id=chat_id, text=f"✅ Successfully added ₹{amount:.2f} to user {target_telegram_id}'s wallet.\nNew Balance: ₹{new_balance:.2f}")

    # Function to handle the /update command (Admin Only)
async def update_price(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the user is the admin
    if str(user_id) != ADMIN_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this command.")
        return

    # Ensure the admin provided the required arguments
    if len(context.args) < 2:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid command format. Use:\n/update <productid> <new_price>")
        return

    # Extract the arguments
    product_id = context.args[0]
    try:
        new_price = float(context.args[1])
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid price. Please provide a valid number.")
        return

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Check if the product exists
    cursor.execute("SELECT productname, price FROM products WHERE productid = ?", (product_id,))
    product = cursor.fetchone()

    if not product:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Product with ID {product_id} not found.")
        conn.close()
        return

    # Update the product price
    cursor.execute("UPDATE products SET price = ? WHERE productid = ?", (new_price, product_id))
    conn.commit()
    conn.close()

    # Send a success message
    await context.bot.send_message(chat_id=chat_id, text=f"✅ Successfully updated the price of '{product[0]}' to ₹{new_price:.2f}.")

# Function to handle the /reseller command (Admin Only)
async def assign_reseller(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the user is the admin
    if str(user_id) != ADMIN_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this command.")
        return

    # Ensure the admin provided the required arguments
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid command format. Use:\n/reseller <telegram_id>")
        return

    # Extract the target Telegram ID
    target_telegram_id = context.args[0]

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Check if the target user exists
    cursor.execute("SELECT role FROM users WHERE uid = ?", (target_telegram_id,))
    user = cursor.fetchone()

    if not user:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ User with Telegram ID {target_telegram_id} not found.")
        conn.close()
        return

    # Update the user's role to "reseller"
    cursor.execute("UPDATE users SET role = 'reseller' WHERE uid = ?", (target_telegram_id,))
    conn.commit()
    conn.close()

    # Send a success message
    await context.bot.send_message(chat_id=chat_id, text=f"✅ User with Telegram ID {target_telegram_id} is now a reseller.") 

    # Function to update the database schema
def update_database_schema():
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Add the reseller_price column to the products table if it doesn't exist
    try:
        cursor.execute("""
            ALTER TABLE products ADD COLUMN reseller_price NUMBER
        """)
        print("reseller_price column added to products table.")
    except sqlite3.OperationalError:
        print("reseller_price column already exists in products table.")

    conn.commit()
    conn.close()
    print("Database schema updated successfully.")
# Function to handle the /resellerprice command (Admin Only)
async def set_reseller_price(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if the user is the admin
    if str(user_id) != ADMIN_ID:
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this command.")
        return

    # Ensure the admin provided the required arguments
    if len(context.args) < 2:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid command format. Use:\n/resellerprice <productid> <reseller_price>")
        return

    # Extract the arguments
    product_id = context.args[0]
    try:
        reseller_price = float(context.args[1])
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid price. Please provide a valid number.")
        return

    # Connect to the database
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()

    # Check if the product exists
    cursor.execute("SELECT productname FROM products WHERE productid = ?", (product_id,))
    product = cursor.fetchone()

    if not product:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Product with ID {product_id} not found.")
        conn.close()
        return

    # Update the reseller price for the product
    cursor.execute("UPDATE products SET reseller_price = ? WHERE productid = ?", (reseller_price, product_id))
    conn.commit()
    conn.close()

    # Send a success message
    await context.bot.send_message(chat_id=chat_id, text=f"✅ Successfully updated the reseller price of '{product[0]}' to ₹{reseller_price:.2f}.")
# Function to handle the /help command
async def help_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Help message with all user commands
    help_message = """
📖 *Help - Available Commands* 📖

✅ *User Commands*:
- `/start` - Register and get started with the bot.
- `/wallet` - Check your wallet balance.
- `/getid` - Get your Telegram ID.
- `/his` - View your order history.
- `/utr <utr>` - Verify BharatPe payment using UTR. 
`Payment UTR` is a unique transaction reference number provided by your bank after a successful payment.


✅ *Product Commands*:
- `/small_pack` - Show available Small Pack Diamonds.
- `/large_pack` - Show available Large Pack Diamonds.
- `/wkp` - Show available Weekly Passes.
- `/bonus` - Show available Bonus Products.

✅ *Order Commands*:
- `/order <userid> <zoneid> <productname>` - Place an order.

✅ *Admin Commands*:
- `/addfund <telegram_id> <amount>` - Add funds to a user's wallet.
- `/update <productid> <new_price>` - Update the price of a product.
- `/reseller <telegram_id>` - Assign a user as a reseller.
- `/resellerprice <productid> <reseller_price>` - Set reseller-specific prices for a product.
- `/addproduct <productname>:<productid>:<price>:<category>` - Add new products.
- `/product_management <productid>:<category>` - Update product categories.
- `/user` - View all registered users.
- `/fatchbr` - Fetch Brazil product list (Admin only).
- `/fatchph` - Fetch Philippines product list (Admin only).

⚠️ *Note*: Commands marked as "Admin Commands" are restricted to the admin user.
"""

    # Send the help message
    await context.bot.send_message(chat_id=chat_id, text=help_message, parse_mode="Markdown")

async def verify_utr(update, context):
    """
    Verify BharatPe payment using UTR and add funds to the user's account.
    """
    # Check if the required arguments are provided
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /utr <utr>")
        return

    # Extract the UTR (Unique Transaction Reference) from the command arguments
    utr = context.args[0].strip()
    user_id = str(update.effective_user.id)

    if not utr:
        await update.message.reply_text("The UTR cannot be empty.")
        return

    # Check if the UTR is already used
    conn = sqlite3.connect("wallet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments WHERE reference = ?", (utr,))
    existing_payment = cursor.fetchone()

    if existing_payment:
        await update.message.reply_text("This UTR is already used.")
        conn.close()
        return

    # Prepare the API request
    from_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    headers = {
        "token": BHARATPE_TOKEN,
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    }
    params = {
        "module": "PAYMENT_QR",
        "merchantId": BHARATPE_MERCHANT_ID,
        "sDate": from_date,
        "eDate": to_date,
    }

    try:
        # Make the API request
        response = requests.get(BHARATPE_API_URL, headers=headers, params=params)
        response_data = response.json()

        # Filter transactions by UTR
        transactions = response_data.get("data", {}).get("transactions", [])
        matching_transaction = next(
            (txn for txn in transactions if txn.get("bankReferenceNo") == utr), None
        )

        if not matching_transaction:
            await update.message.reply_text("UTR verification failed. Please try again later.")
            conn.close()
            return

        # Verify the transaction details
        if matching_transaction.get("status") == "SUCCESS":
            amount = float(matching_transaction.get("amount", 0.0))

            # Add funds to the user's wallet
            cursor.execute("SELECT balance FROM users WHERE userid = ?", (user_id,))
            user_data = cursor.fetchone()

            if not user_data:
                await update.message.reply_text("User not found. Please register using /start.")
                conn.close()
                return

            current_balance = user_data[0]
            new_balance = current_balance + amount

            # Update the user's wallet balance
            cursor.execute("UPDATE users SET balance = ? WHERE userid = ?", (new_balance, user_id))

            # Insert the payment record
            cursor.execute(
                """
                INSERT INTO payments (userid, amount, reference, status, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, amount, utr, "VERIFIED", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            conn.close()

            # Notify the user
            await update.message.reply_text(
                f"Payment verified successfully! ₹{amount:.2f} has been added to your wallet. Current balance: ₹{new_balance:.2f}"
            )
        else:
            await update.message.reply_text("UTR verification failed. Please try again later.")
            conn.close()
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"An error occurred while verifying the payment: {e}")
        conn.close()
    
# Add the /addproduct command handler to the bot
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("wallet", wallet))
application.add_handler(CommandHandler("getid", getid))  # Now the getid function is defined before this line
application.add_handler(CommandHandler("user", user))
application.add_handler(CommandHandler("order", order_command))
application.add_handler(CommandHandler("addproduct", add_product))
application.add_handler(CommandHandler("product_management", product_management))
application.add_handler(CommandHandler("small_pack", small_pack))
application.add_handler(CommandHandler("large_pack", large_pack))
application.add_handler(CommandHandler("wkp", wkp))
application.add_handler(CommandHandler("bonus", bonus))
application.add_handler(CommandHandler("his", order_history))
application.add_handler(CommandHandler("fatchbr", fetch_br_products))
application.add_handler(CommandHandler("fatchph", fetch_ph_products))
application.add_handler(CommandHandler("update", update_price))
application.add_handler(CommandHandler("addfund", add_fund))
application.add_handler(CommandHandler("reseller", assign_reseller))
application.add_handler(CommandHandler("resellerprice", set_reseller_price))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("utr", verify_utr))
# Run the bot
application.run_polling()