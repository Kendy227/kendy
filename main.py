import time
import hmac
import hashlib
import base64
import json
import sqlite3
import requests
from datetime import datetime
from telebot import TeleBot
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# Configuration
TOKEN = "8186293444:AAHMOlDF_CmvhpcVCsaom4ugLnHSP7GHBzk"
PARTNER_ID = "d2c1ab6c0b58488fbd1ee0d7de0511e9"
SECRET_KEY = "ha61HJLMhO"
MOOGOLD_API_URL = "https://moogold.com/wp-json/v1/api/"
ADMIN_ID = 6501929376
BOT_NAME = "Kendy Enterprises"
DB_PATH = "wallet.db"

# Initialize bot
bot = TeleBot(TOKEN, parse_mode="MARKDOWN")

# Database Setup
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                joined DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT,
                price REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                product_id TEXT,
                total REAL,
                status TEXT DEFAULT 'pending',
                created DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

init_db()

# Helper Functions
def generate_auth_signature(payload, timestamp, path):
    """Generate HMAC-SHA256 signature for MooGold API."""
    string_to_sign = payload + timestamp + path
    return hmac.new(
        bytes(SECRET_KEY, 'utf-8'),
        msg=string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

def is_admin(user_id):
    return user_id == ADMIN_ID

# --------------------
# ADMIN COMMANDS
# --------------------

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized to access the admin panel.")
        return
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("View Users", callback_data="admin_users"),
               InlineKeyboardButton("Add Funds", callback_data="admin_add"))
    markup.add(InlineKeyboardButton("Add Product", callback_data="admin_add_product"),
               InlineKeyboardButton("List Products", callback_data="admin_list_products"))
    bot.reply_to(message, "🔐 ADMIN PANEL", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_actions(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Unauthorized")
        return

    action = call.data.split("_")[1]
    if action == "users":
        with sqlite3.connect(DB_PATH) as conn:
            users = conn.execute("SELECT user_id, username, balance FROM users").fetchall()
        if not users:
            bot.send_message(call.message.chat.id, "No users found.")
        else:
            response = "\n".join([f"ID: {u[0]}, Username: {u[1]}, Balance: ₹{u[2]:.2f}" for u in users])
            bot.send_message(call.message.chat.id, f"👥 Registered Users:\n{response}")
    elif action == "add_product":
        bot.send_message(call.message.chat.id, "Use /add_product <PRODUCT_ID> <NAME> <PRICE> to add a product.")
    elif action == "list_products":
        with sqlite3.connect(DB_PATH) as conn:
            products = conn.execute("SELECT product_id, name, price FROM products").fetchall()
        if not products:
            bot.send_message(call.message.chat.id, "No products available.")
        else:
            response = "\n".join([f"ID: {p[0]}, Name: {p[1]}, Price: ₹{p[2]:.2f}" for p in products])
            bot.send_message(call.message.chat.id, f"📦 Products:\n{response}")

@bot.message_handler(commands=['add_product'])
def add_product(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized to add products.")
        return

    try:
        args = message.text.split()[1:]
        if len(args) != 3:
            bot.reply_to(message, "Usage: /add_product <PRODUCT_ID> <NAME> <PRICE>")
            return

        product_id, name, price = args
        price = float(price)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT OR REPLACE INTO products (product_id, name, price) VALUES (?, ?, ?)",
                         (product_id, name, price))
        bot.reply_to(message, f"✅ Product '{name}' added successfully!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# --------------------
# USER COMMANDS
# --------------------

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user.id, user.username))
    bot.reply_to(message, f"🚀 Welcome to {BOT_NAME}!\n\nUse /help to see available commands.")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, """
🔍 Commands:
/start - Start the bot
/help - Show this help message
/balance - Check wallet balance
/products - View available products
""")

@bot.message_handler(commands=['balance'])
def balance(message):
    with sqlite3.connect(DB_PATH) as conn:
        balance = conn.execute("SELECT balance FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    balance = balance[0] if balance else 0.0
    bot.reply_to(message, f"💰 Your wallet balance: ₹{balance:.2f}")

@bot.message_handler(commands=['products'])
def products(message):
    with sqlite3.connect(DB_PATH) as conn:
        products = conn.execute("SELECT product_id, name, price FROM products").fetchall()
    if not products:
        bot.reply_to(message, "❌ No products available.")
    else:
        response = "\n".join([f"ID: {p[0]}, Name: {p[1]}, Price: ₹{p[2]:.2f}" for p in products])
        bot.reply_to(message, f"📦 Available Products:\n{response}")

# --------------------
# SYSTEM FUNCTIONS
# --------------------

def set_commands():
    user_cmds = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help message"),
        BotCommand("balance", "Check wallet balance"),
        BotCommand("products", "View available products")
    ]
    admin_cmds = user_cmds + [
        BotCommand("admin", "Admin control panel"),
        BotCommand("add_product", "Add a new product")
    ]
    bot.set_my_commands(user_cmds)
    bot.set_my_commands(commands=admin_cmds, scope=telebot.types.BotCommandScopeChat(chat_id=ADMIN_ID))

if __name__ == "__main__":
    set_commands()
    print(f"🤖 {BOT_NAME} is operational!")
    bot.infinity_polling()
