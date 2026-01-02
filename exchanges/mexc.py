"""
MEXC Exchange Implementation.
"""
import requests
import logging
from typing import List, Dict
from .base import Exchange

logger = logging.getLogger(__name__)

class MexcExchange(Exchange):
    def __init__(self):
        super().__init__('MEXC', 'https://api.mexc.com')
        self.session = requests.Session()

    def _get(self, endpoint: str):
        try:
            url = f"{self.base_url}{endpoint}"
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"MEXC API Error: {e}")
            return None

    def fetch_symbols(self) -> List[Dict]:
        data = self._get("/api/v3/exchangeInfo")
        if not data: return []
        
        symbols = []
        for s in data.get('symbols', []):
            if s.get('status') == '1' and s.get('isSpotTradingAllowed', True):
                # Fee handling: Try to get from API or default
                # MEXC might return 'takerCommission' in this endpoint
                try:
                    taker = self.safe_float(s.get('takerCommission'), 0.001)
                    maker = self.safe_float(s.get('makerCommission'), 0.001)
                except:
                    taker = 0.001
                    maker = 0.001
                
                # Limits
                min_base = 0.0
                min_quote = 0.0
                for f in s.get('filters', []):
                     if f['filterType'] == 'LOT_SIZE': min_base = self.safe_float(f.get('minQty'))
                     if f['filterType'] in ['MIN_NOTIONAL', 'NOTIONAL']: min_quote = self.safe_float(f.get('minNotional'))

                symbols.append({
                    'symbol': s['symbol'],
                    'base': s['baseAsset'],
                    'quote': s['quoteAsset'],
                    'fee_maker': maker,
                    'fee_taker': taker,
                    'min_base': min_base,
                    'min_quote': min_quote,
                    'original': s
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
