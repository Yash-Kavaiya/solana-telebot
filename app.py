import telebot
import requests
import base58
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_logs.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize your Telegram bot with your bot token
BOT_TOKEN = '7332216298:AAEj0787aEQPDjd7qJqgLgzW7ha6l5p7dTs'
bot = telebot.TeleBot(BOT_TOKEN)

# Solana RPC endpoint
SOLANA_RPC_URL = "https://api.devnet.solana.com"

def is_valid_solana_address(address):
    logger.info(f"Validating Solana address: {address}")
    try:
        decoded = base58.b58decode(address)
        is_valid = len(decoded) == 32
        logger.info(f"Address validation result: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Address validation error: {str(e)}")
        return False

def get_solana_balance(address):
    logger.info(f"Fetching balance for address: {address}")
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [address]
    }
    
    try:
        logger.info(f"Making RPC request to {SOLANA_RPC_URL}")
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(SOLANA_RPC_URL, headers=headers, json=payload)
        response_json = response.json()
        
        logger.info(f"RPC response received. Status code: {response.status_code}")
        logger.debug(f"Response data: {json.dumps(response_json, indent=2)}")
        
        return response_json
    except Exception as e:
        logger.error(f"RPC request failed: {str(e)}")
        raise

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    logger.info(f"New user started bot - ID: {user_id}, Username: @{username}")
    
    welcome_msg = "👋 Welcome! I can help you check your Solana wallet balance.\n\nPlease enter your Solana wallet address."
    bot.reply_to(message, welcome_msg)
    logger.info(f"Sent welcome message to user {user_id}")

@bot.message_handler(func=lambda message: True)
def handle_wallet_address(message):
    user_id = message.from_user.id
    username = message.from_user.username
    wallet_address = message.text.strip()
    
    logger.info(f"Processing wallet request - User ID: {user_id}, Username: @{username}")
    logger.info(f"Received wallet address: {wallet_address}")
    
    if not is_valid_solana_address(wallet_address):
        logger.warning(f"Invalid address provided by user {user_id}: {wallet_address}")
        bot.reply_to(message, "❌ Invalid Solana wallet address. Please enter a valid address.")
        return
    
    try:
        logger.info(f"Fetching balance for valid address: {wallet_address}")
        response = get_solana_balance(wallet_address)
        
        if 'result' in response and 'value' in response['result']:
            balance_in_lamports = response['result']['value']
            balance_in_sol = balance_in_lamports / 1_000_000_000
            response_msg = f"💰 Wallet Balance:\n{balance_in_sol:.9f} SOL"
            logger.info(f"Balance retrieved successfully - Address: {wallet_address}, Balance: {balance_in_sol} SOL")
        else:
            response_msg = "Account not found or has no balance."
            logger.warning(f"No balance found for address: {wallet_address}")
            
        bot.reply_to(message, response_msg)
        logger.info(f"Sent balance response to user {user_id}")
        
    except Exception as e:
        error_msg = f"❌ Error fetching wallet balance: {str(e)}"
        logger.error(f"Error processing request for user {user_id}: {str(e)}", exc_info=True)
        bot.reply_to(message, error_msg)

def main():
    logger.info("=== Bot Starting ===")
    logger.info(f"Start Time: {datetime.now()}")
    logger.info(f"Bot Username: @{bot.get_me().username}")
    
    try:
        logger.info("Starting bot polling...")
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Critical bot error: {str(e)}", exc_info=True)
    finally:
        logger.info("=== Bot Stopped ===")

if __name__ == "__main__":
    main()
