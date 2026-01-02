"""
Configuration settings for the Multi-Exchange Arbitrage Bot.
"""

# Enabled Exchanges (Can be toggled via API/UI in future)
# Options: 'MEXC', 'Binance', 'KuCoin', 'Bybit', 'HTX'
ENABLED_EXCHANGES = ['MEXC', 'Binance', 'KuCoin', 'Bybit', 'HTX']

# Global Fee Fallback (if API doesn't return fee)
DEFAULT_FEE_RATE = 0.001 

# Arbitrage Search Settings
START_AMOUNT = 100.0
MIN_PROFIT_PERCENT = -0.5 # Slight loss allowed for visibility
MAX_DEPTH = 2
MIN_TRADES = 2

# Supported Stablecoins
STABLECOINS = [
    "USDT",
    "USDC"
]

REQUEST_TIMEOUT = 10

# Trading Execution Config
TRADE_MODE = 'PAPER' # 'PAPER' or 'LIVE_TESTNET'
BYBIT_API_KEY = ''
BYBIT_API_SECRET = ''
