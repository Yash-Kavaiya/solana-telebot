from abc import ABC, abstractmethod
import telebot
import requests
import base58
import logging
import json
from datetime import datetime
import sqlite3
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import threading
from functools import wraps
import time

# Constants
class Config:
    BOT_TOKEN = '7332216298:AAEj0787aEQPDjd7qJqgLgzW7ha6l5p7dTs'
    SOLANA_MAINNET_URL = "https://api.mainnet-beta.solana.com"
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
    DB_PATH = 'bot_metrics.db'
    LOG_PATH = 'bot.log'

# Domain Models
@dataclass
class WalletBalance:
    address: str
    sol_balance: float
    usd_value: Optional[float] = None

@dataclass
class UserRequest:
    user_id: int
    username: str
    wallet_address: str
    timestamp: datetime

# Interfaces
class IDatabase(ABC):
    @abstractmethod
    def save_metrics(self, metrics: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        pass

class IBlockchainClient(ABC):
    @abstractmethod
    def get_balance(self, address: str) -> float:
        pass

class IPriceOracle(ABC):
    @abstractmethod
    def get_sol_price(self) -> Optional[float]:
        pass

# Implementations
class SQLiteDatabase(IDatabase):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    timestamp TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    PRIMARY KEY (timestamp, metric_name)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallet_checks (
                    address TEXT,
                    timestamp TEXT,
                    balance REAL,
                    user_id INTEGER
                )
            ''')

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def save_metrics(self, metrics: Dict[str, Any]) -> None:
        timestamp = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for metric_name, value in metrics.items():
                cursor.execute(
                    'INSERT OR REPLACE INTO metrics VALUES (?, ?, ?)',
                    (timestamp, metric_name, float(value))
                )

    def get_metrics(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT metric_name, metric_value FROM metrics WHERE timestamp = (SELECT MAX(timestamp) FROM metrics)'
            )
            return dict(cursor.fetchall())

class SolanaClient(IBlockchainClient):
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url

    def get_balance(self, address: str) -> float:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }
        response = requests.post(self.rpc_url, json=payload)
        response.raise_for_status()
        data = response.json()
        if 'result' not in data or 'value' not in data['result']:
            raise ValueError("Invalid response from Solana RPC")
        return data['result']['value'] / 1_000_000_000  # Convert lamports to SOL

class CoinGeckoPriceOracle(IPriceOracle):
    def __init__(self, api_url: str):
        self.api_url = api_url

    def get_sol_price(self) -> Optional[float]:
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()
            return data['solana']['usd']
        except Exception as e:
            logging.error(f"Error fetching SOL price: {e}")
            return None

# Service Layer
class MetricsService:
    def __init__(self, database: IDatabase):
        self.database = database
        self.metrics = {
            'total_requests': 0,
            'active_users': set(),
            'unique_addresses': set(),
            'total_sol_checked': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
        self._lock = threading.Lock()

    def update_metric(self, metric_name: str, value: Any) -> None:
        with self._lock:
            if isinstance(self.metrics[metric_name], set):
                self.metrics[metric_name].add(value)
            else:
                self.metrics[metric_name] += value

    def save_current_metrics(self) -> None:
        metrics_to_save = {}
        with self._lock:
            for metric, value in self.metrics.items():
                metrics_to_save[metric] = len(value) if isinstance(value, set) else value
        self.database.save_metrics(metrics_to_save)

class WalletService:
    def __init__(
        self,
        blockchain_client: IBlockchainClient,
        price_oracle: IPriceOracle
    ):
        self.blockchain_client = blockchain_client
        self.price_oracle = price_oracle

    @staticmethod
    def is_valid_address(address: str) -> bool:
        try:
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except Exception:
            return False

    def get_wallet_balance(self, address: str) -> WalletBalance:
        sol_balance = self.blockchain_client.get_balance(address)
        sol_price = self.price_oracle.get_sol_price()
        usd_value = sol_balance * sol_price if sol_price else None
        return WalletBalance(address, sol_balance, usd_value)

# Telegram Bot Implementation
class SolanaBot:
    def __init__(
        self,
        token: str,
        wallet_service: WalletService,
        metrics_service: MetricsService
    ):
        self.bot = telebot.TeleBot(token)
        self.wallet_service = wallet_service
        self.metrics_service = metrics_service
        self._setup_handlers()
        self._setup_metrics_saving()

    def _setup_metrics_saving(self) -> None:
        def save_metrics_periodically():
            while True:
                self.metrics_service.save_current_metrics()
                time.sleep(60)
        
        thread = threading.Thread(
            target=save_metrics_periodically,
            daemon=True
        )
        thread.start()

    def _setup_handlers(self) -> None:
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            self.metrics_service.update_metric('active_users', user_id)
            welcome_msg = (
                "👋 Welcome to Solana Balance Checker!\n\n"
                "I can help you check your Solana wallet balance on Mainnet.\n"
                "Please enter your Solana wallet address."
            )
            self.bot.reply_to(message, welcome_msg)

        @self.bot.message_handler(func=lambda m: True)
        def handle_wallet_address(message):
            try:
                self._process_wallet_request(message)
            except Exception as e:
                logging.error(f"Error processing request: {e}", exc_info=True)
                self.bot.reply_to(
                    message,
                    "❌ An error occurred while processing your request."
                )

    def _process_wallet_request(self, message) -> None:
        user_id = message.from_user.id
        wallet_address = message.text.strip()
        
        self.metrics_service.update_metric('total_requests', 1)
        
        if not self.wallet_service.is_valid_address(wallet_address):
            self.metrics_service.update_metric('failed_requests', 1)
            self.bot.reply_to(
                message,
                "❌ Invalid Solana wallet address. Please enter a valid address."
            )
            return

        try:
            balance = self.wallet_service.get_wallet_balance(wallet_address)
            self.metrics_service.update_metric('successful_requests', 1)
            self.metrics_service.update_metric('unique_addresses', wallet_address)
            self.metrics_service.update_metric('total_sol_checked', balance.sol_balance)

            response_msg = (
                f"💰 Wallet Balance for:\n"
                f"`{balance.address}`\n\n"
                f"Balance: **{balance.sol_balance:.4f} SOL**\n"
            )

            if balance.usd_value:
                response_msg += f"Value: **${balance.usd_value:.2f} USD**\n"

            response_msg += "\n_Checked on Solana Mainnet_"
            
            self.bot.reply_to(message, response_msg, parse_mode='Markdown')
            
        except Exception as e:
            self.metrics_service.update_metric('failed_requests', 1)
            raise

    def run(self) -> None:
        logging.info("Starting Solana Balance Bot...")
        self.bot.polling(none_stop=True)

# Main Application
def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_PATH),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    
    # Initialize dependencies
    database = SQLiteDatabase(Config.DB_PATH)
    blockchain_client = SolanaClient(Config.SOLANA_MAINNET_URL)
    price_oracle = CoinGeckoPriceOracle(Config.COINGECKO_API_URL)
    
    # Initialize services
    metrics_service = MetricsService(database)
    wallet_service = WalletService(blockchain_client, price_oracle)
    
    # Initialize and run bot
    bot = SolanaBot(Config.BOT_TOKEN, wallet_service, metrics_service)
    
    try:
        bot.run()
    except Exception as e:
        logging.error(f"Critical error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
