"""
Binance Exchange Implementation.
"""
import requests
import logging
from typing import List, Dict
from .base import Exchange

logger = logging.getLogger(__name__)

class BinanceExchange(Exchange):
    def __init__(self):
        super().__init__('Binance', 'https://api.binance.com')
        self.session = requests.Session()

    def _get(self, endpoint: str):
        try:
            url = f"{self.base_url}{endpoint}"
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Binance API Error: {e}")
            return None

    def fetch_symbols(self) -> List[Dict]:
        data = self._get("/api/v3/exchangeInfo")
        if not data: return []
        
        symbols = []
        for s in data.get('symbols', []):
            if s.get('status') == 'TRADING':
                # Binance fees are usually user-specific via /account or default 0.1%
                # Public info doesn't always have fees per pair.
                # We assume standard 0.1% if not authenticated/found.
                # Some pairs (TUSD/USDT) might have 0 fees. This implies hardcoding or advanced fetching.
                # Per prompt: "Fetch live... Maker fee, Taker fee".
                # Without auth, we can't reliably get *personal* fees. 
                # We will use 0.001 (0.1%) as standard.
                maker = 0.001
                taker = 0.001
                
                # Check for 0 fee pairs (common known ones or just use default)
                if s['quoteAsset'] in ['FDUSD', 'TUSD'] and s['baseAsset'] in ['BTC', 'ETH']:
                     # Heuristic for known promos? Safer to stick to conservative 0.1%
                     pass

                min_base = 0.0
                min_quote = 0.0
                for f in s.get('filters', []):
                     if f['filterType'] == 'LOT_SIZE': min_base = float(f.get('minQty', 0))
                     if f['filterType'] == 'NOTIONAL': min_quote = float(f.get('minNotional', 0))

                symbols.append({
                    'symbol': s['symbol'],
                    'base': s['baseAsset'],
                    'quote': s['quoteAsset'],
                    'fee_maker': maker,
                    'fee_taker': taker,
                    'min_base': min_base,
                    'min_quote': min_quote
                })
        return symbols

    def fetch_tickers(self) -> Dict[str, Dict]:
        data = self._get("/api/v3/ticker/bookTicker")
        if not data: return {}
        
        tickers = {}
        for t in data:
            tickers[t['symbol']] = {
                'bid': self.safe_float(t.get('bidPrice'), 0.0),
                'ask': self.safe_float(t.get('askPrice'), 0.0),
                'bidQty': self.safe_float(t.get('bidQty'), 0.0),
                'askQty': self.safe_float(t.get('askQty'), 0.0)
            }
        return tickers
