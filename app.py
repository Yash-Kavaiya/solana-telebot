import os
import telebot
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize bot
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

# Headers for Solscan API
headers = {
    'token': os.getenv('SOLSCAN_API_KEY')
}

def validate_solana_address(address):
    return len(address) == 44 or len(address) == 43

def get_wallet_balance(address):
    try:
        url = f"https://public-api.solscan.io/account/{address}"
        response = requests.get(url, headers=headers)
        data = response.json()
        return float(data.get('lamports', 0)) / 1000000000  # Convert lamports to SOL
    except Exception as e:
        return None

def get_recent_transactions(address):
    try:
        url = f"https://public-api.solscan.io/account/transactions?account={address}&limit=5"
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "Welcome! Send me a Solana wallet address to check its balance and recent transactions."
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_wallet_address(message):
    address = message.text.strip()
    
    if not validate_solana_address(address):
        bot.reply_to(message, "❌ Invalid Solana address format. Please try again.")
        return

    # Get wallet balance
    balance = get_wallet_balance(address)
    if balance is None:
        bot.reply_to(message, "❌ Error fetching wallet balance. Please try again later.")
        return

    # Get recent transactions
    transactions = get_recent_transactions(address)
    if transactions is None:
        bot.reply_to(message, "❌ Error fetching transactions. Please try again later.")
        return

    # Format response
    response = f"💰 *Wallet Details*\n"
    response += f"Address: `{address}`\n"
    response += f"Balance: {balance:.4f} SOL\n\n"
    
    response += "📝 *Recent Transactions*\n"
    for tx in transactions[:5]:
        timestamp = datetime.fromtimestamp(tx.get('blockTime', 0))
        response += f"• Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        response += f"  Signature: `{tx.get('signature', '')[:20]}...`\n"
        response += f"  Status: {'✅ Success' if tx.get('status') == 'Success' else '❌ Failed'}\n\n"

    bot.reply_to(message, response, parse_mode="Markdown")

# Start the bot
if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
