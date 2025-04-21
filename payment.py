from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import threading
import qrcode
import os
import time
import uuid  # Add this import for generating unique reference numbers

# Replace with your bot token
BOT_TOKEN = "7862686786:AAFm0kOB54vYgoQAjsI81GWB4egTz07Hiz4"
UPI_ID = "9366673633@okbizaxis"  # Google Pay Business UPI ID
PAYEE_NAME = "Google Pay Merchant"
CURRENCY = "INR"
MERCHANT_ID = "BCR2DN4TY3FYXKQD"

# Flask app for API
app = Flask(__name__)

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# In-memory wallet storage (use a database in production)
user_wallets = {}
pending_payments = {}

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message and instructions."""
    await update.message.reply_text(
        "Welcome to the Payment Gateway Bot!\n"
        "Use /pay <amount> to make a payment.\n"
        "Use /wallet to check your wallet balance."
    )

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check wallet balance."""
    chat_id = update.message.chat_id
    balance = user_wallets.get(chat_id, 0)  # Default balance is 0
    await update.message.reply_text(f"Your wallet balance is: ₹{balance:.2f}")

async def pay_with_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send UPI payment options with a QR code and clickable button."""
    chat_id = update.message.chat_id

    # Check if the user provided an amount
    if len(context.args) == 0:
        await update.message.reply_text("Please provide an amount to pay. Example: /pay 100")
        return

    try:
        # Parse the amount from the command arguments
        amount = float(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be greater than 0.")
    except ValueError:
        await update.message.reply_text("Invalid amount. Please provide a valid number. Example: /pay 100")
        return

    # Generate a unique reference number
    reference_number = str(uuid.uuid4())[:8]  # Shorten UUID to 8 characters

    # Include Telegram ID and reference number in the transaction note
    transaction_note = f"Ref: {reference_number}, ID: {chat_id}"

    # Generate UPI payment link
    upi_link = (
        f"upi://pay?pa={UPI_ID}&pn={PAYEE_NAME}&am={amount}&cu={CURRENCY}&tn={transaction_note}&mc={MERCHANT_ID}"
    )

    # Add to pending payments
    pending_payments[chat_id] = {"amount": amount, "status": "pending", "reference": reference_number}

    # Generate QR code for the UPI link
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_link)
    qr.make(fit=True)
    qr_image_path = f"upi_qr_{chat_id}.png"
    qr_image = qr.make_image(fill="black", back_color="white")
    qr_image.save(qr_image_path)

    # Send QR code image
    await context.bot.send_photo(chat_id=chat_id, photo=open(qr_image_path, "rb"))

    # Send clickable button
    keyboard = [
        [InlineKeyboardButton("Pay via UPI App", url=upi_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Scan the QR code above or click the button below to pay via your UPI app.\n"
        f"Reference Number: {reference_number}\n"
        f"Once the payment is complete, it will be verified automatically.",
        reply_markup=reply_markup
    )

    # Countdown timer for QR code expiration
    for remaining_time in range(240, 0, -60):  # Countdown in 60-second intervals
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"QR code will expire in {remaining_time // 60} minutes."
        )
        time.sleep(60)

    # Notify the user that the QR code has expired
    await context.bot.send_message(
        chat_id=chat_id,
        text="The QR code has expired. Please generate a new one if you still wish to make a payment."
    )

    # Schedule QR code deletion after 4 minutes
    threading.Timer(240, delete_qr_code, args=(qr_image_path,)).start()

def delete_qr_code(file_path):
    """Delete the QR code file after 4 minutes."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"QR code file {file_path} deleted successfully.")
    except Exception as e:
        print(f"Error deleting QR code file {file_path}: {e}")

def verify_payments():
    """Background task to verify payments."""
    while True:
        # Simulate checking payment status (replace with actual API calls)
        for chat_id, payment in list(pending_payments.items()):
            if payment["status"] == "pending":
                if check_payment_status(chat_id, payment["amount"]):  # Replace with actual logic
                    # Update wallet balance
                    if chat_id in user_wallets:
                        user_wallets[chat_id] += payment["amount"]
                    else:
                        user_wallets[chat_id] = payment["amount"]

                    # Notify the user
                    bot = Bot(token=BOT_TOKEN)
                    bot.send_message(
                        chat_id=chat_id,
                        text=f"Payment of ₹{payment['amount']:.2f} has been verified and added to your wallet.\n"
                             f"Reference Number: {payment['reference']}\n"
                             f"Your new wallet balance is: ₹{user_wallets[chat_id]:.2f}"
                    )

                    # Remove from pending payments
                    del pending_payments[chat_id]
                else:
                    # Notify the user of payment failure
                    bot = Bot(token=BOT_TOKEN)
                    bot.send_message(
                        chat_id=chat_id,
                        text=f"Payment of ₹{payment['amount']:.2f} failed.\n"
                             f"Reference Number: {payment['reference']}\n"
                             f"Please try again."
                    )

                    # Remove from pending payments
                    del pending_payments[chat_id]

        time.sleep(60)  # Check every 60 seconds

def check_payment_status(chat_id, amount):
    """Simulate payment verification (replace with actual API logic)."""
    # Replace this with actual logic to verify payments using UPI provider's API or logs
    # For now, simulate that payments are verified after 1 minute
    return True

def run_flask():
    """Run the Flask app."""
    app.run(host="0.0.0.0", port=8080)

def main():
    """Run the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pay", pay_with_upi))  # Use UPI payment
    application.add_handler(CommandHandler("wallet", wallet))  # Check wallet balance

    # Run Flask in a separate thread
    threading.Thread(target=run_flask).start()

    # Start the background task
    threading.Thread(target=verify_payments, daemon=True).start()

    application.run_polling()

if __name__ == "__main__":
    main()