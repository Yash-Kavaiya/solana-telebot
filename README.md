# Solana Balance Checker Telegram Bot

A production-ready Telegram bot that checks Solana wallet balances with real-time USD conversion and comprehensive metrics tracking. Built using SOLID principles and modern Python practices.

## 🌟 Features

- Real-time Solana wallet balance checking
- Automatic USD value conversion
- Production-grade error handling and logging
- Comprehensive metrics tracking
- Thread-safe operations
- Price caching to minimize API calls
- SQLite database for metrics storage
- SOLID principles implementation
- Fully typed with Python type hints

## 📋 Prerequisites

- Python 3.9+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Internet connection for API access

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/solana-balance-bot.git
cd solana-balance-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
BOT_TOKEN=your_telegram_bot_token
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

## 🚀 Usage

1. Start the bot:
```bash
python bot.py
```

2. In Telegram, start a chat with your bot and send a Solana wallet address.

3. The bot will respond with:
   - Current SOL balance
   - USD value
   - Timestamp of the check

## 🏗️ Project Structure

```
solana-balance-bot/
├── bot.py              # Main bot implementation
├── requirements.txt    # Project dependencies
├── .env               # Environment variables
├── bot_metrics.db     # SQLite database for metrics
├── bot.log            # Application logs
└── README.md          # Project documentation
```

## 📚 Code Architecture

### Core Components

1. **SolanaBot**
   - Main bot class
   - Handles Telegram interactions
   - Coordinates other components

2. **SolanaRPCClient**
   - Manages Solana blockchain interactions
   - Handles RPC calls
   - Converts lamports to SOL

3. **PriceService**
   - Abstract base class for price services
   - CoingeckoPriceService implementation
   - Includes price caching

4. **MetricsCollector**
   - Tracks bot usage metrics
   - Thread-safe operations
   - Stores metrics in SQLite

5. **WalletValidator**
   - Validates Solana addresses
   - Base58 check implementation

### Data Models

```python
@dataclass
class WalletBalance:
    address: str
    sol_balance: float
    usd_value: float
    timestamp: datetime
```

### Database Schema

```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

## 📊 Metrics Tracked

- Total requests
- Successful requests
- Failed requests
- Total SOL checked
- Request timestamps
- Response times

## 🔒 Security Features

1. **Environment Variables**
   - Sensitive data stored in .env
   - No hardcoded tokens/keys

2. **Error Handling**
   - Comprehensive try-catch blocks
   - Detailed error logging
   - User-friendly error messages

3. **Rate Limiting**
   - Price API caching
   - Configurable cache duration

## 📝 Logging

Logs are stored in `bot.log` with the following format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Log levels:
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Operation failures
- CRITICAL: System failures

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| BOT_TOKEN | Telegram Bot Token | Required |
| SOLANA_RPC_URL | Solana RPC endpoint | https://api.mainnet-beta.solana.com |

### Configurable Parameters

```python
class CoingeckoPriceService:
    cache_duration = 60  # Price cache duration in seconds

class MetricsCollector:
    metrics = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'total_sol_checked': 0
    }
```

## 🧪 Testing

1. Run unit tests:
```bash
python -m pytest tests/
```

2. Run integration tests:
```bash
python -m pytest tests/integration/
```

## 🔄 Development Workflow

1. Create feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and test

3. Update documentation if needed

4. Create pull request

## 🐛 Troubleshooting

Common issues and solutions:

1. **Connection Errors**
   - Check internet connection
   - Verify RPC endpoint status
   - Ensure valid bot token

2. **Database Errors**
   - Check write permissions
   - Verify database file location
   - Check disk space

3. **API Rate Limits**
   - Monitor Coingecko API usage
   - Adjust cache duration if needed
   - Check for multiple instances

## 📈 Performance Considerations

- Price caching reduces API calls
- Thread-safe operations for concurrent users
- Efficient database operations
- Minimal memory footprint
- Optimized balance calculations

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 👥 Contact

- Author: Your Name
- Email: your.email@example.com
- Telegram: @your_telegram_username

## 🙏 Acknowledgments

- Solana Foundation for RPC endpoints
- CoinGecko for price API
- Telegram for bot API

## 🔄 Changelog

### v1.0.0 (2025-01-18)
- Initial release
- Basic wallet balance checking
- USD conversion
- Metrics tracking

## 🗺️ Roadmap

- [ ] Add support for SPL tokens
- [ ] Implement wallet transaction history
- [ ] Add multi-language support
- [ ] Create web dashboard for metrics
- [ ] Add support for other price APIs
