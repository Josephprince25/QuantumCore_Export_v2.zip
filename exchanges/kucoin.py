"""
KuCoin Exchange Implementation.
"""
import requests
import logging
from typing import List, Dict
from .base import Exchange

logger = logging.getLogger(__name__)

class KuCoinExchange(Exchange):
    def __init__(self):
        super().__init__('KuCoin', 'https://api.kucoin.com')
        self.session = requests.Session()

    def _get(self, endpoint: str):
        try:
            url = f"{self.base_url}{endpoint}"
            # KuCoin sometimes needs headers
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"KuCoin API Error: {e}")
            return None

    def fetch_symbols(self) -> List[Dict]:
        data = self._get("/api/v1/symbols")
        if not data or data.get('code') != '200000': return []
        
        symbols = []
        for s in data.get('data', []):
            if s.get('enableTrading'):
                # KuCoin fees: 0.1% standard
                maker = 0.001
                taker = 0.001
                
                # Try to parse limits
                min_base = float(s.get('baseMinSize', 0))
                min_quote = float(s.get('quoteMinSize', 0)) # Might be minFunds

                symbols.append({
                    'symbol': s['symbol'], # internal uses hyphens e.g. BTC-USDT
                    'base': s['baseCurrency'],
                    'quote': s['quoteCurrency'],
                    'fee_maker': maker,
                    'fee_taker': taker,
                    'min_base': min_base,
                    'min_quote': min_quote,
                    'normalized_symbol': s['symbol'].replace('-', '') # For uniformity if needed?
                })
        return symbols

    def fetch_tickers(self) -> Dict[str, Dict]:
        data = self._get("/api/v1/market/allTickers")
        if not data or data.get('code') != '200000': return {}
        
        tickers = {}
        for t in data.get('data', {}).get('ticker', []):
             # KuCoin allTickers structure: {symbol: "BTC-USDT", buy: "...", sell: "...", ...}
             sym = t.get('symbol')
             tickers[sym] = {
                'bid': float(t.get('buy', 0) or 0),
                'ask': float(t.get('sell', 0) or 0),
                'bidQty': 0, # not provided in allTickers summary easily
                'askQty': 0
             }
        return tickers
