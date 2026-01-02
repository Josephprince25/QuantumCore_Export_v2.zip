"""
HTX (Huobi) Exchange Implementation.
"""
import requests
import logging
from typing import List, Dict
from .base import Exchange

logger = logging.getLogger(__name__)

class HTXExchange(Exchange):
    def __init__(self):
        super().__init__('HTX', 'https://api.htx.com')
        self.session = requests.Session()

    def _get(self, endpoint: str):
        try:
            url = f"{self.base_url}{endpoint}"
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"HTX API Error: {e}")
            return None

    def fetch_symbols(self) -> List[Dict]:
        data = self._get("/v1/common/symbols")
        if not data or data.get('status') != 'ok': return []
        
        symbols = []
        for s in data.get('data', []):
            if s.get('state') == 'online':
                maker = 0.002 # HTX often 0.2% base
                taker = 0.002
                
                symbols.append({
                    'symbol': s['symbol'], # lowercase usually in htx api? e.g. 'btcusdt'
                    'base': s['base-currency'].upper(),
                    'quote': s['quote-currency'].upper(),
                    'fee_maker': maker,
                    'fee_taker': taker,
                    'min_base': float(s.get('min-order-amt', 0)),
                    'min_quote': float(s.get('min-order-value', 0))
                })
        return symbols

    def fetch_tickers(self) -> Dict[str, Dict]:
        data = self._get("/market/tickers")
        if not data or data.get('status') != 'ok': return {}
        
        tickers = {}
        for t in data.get('data', []):
            # HTX symbol is lowercase e.g. "btcusdt"
            sym = t['symbol']
            tickers[sym] = {
                'bid': float(t.get('bid', 0)),
                'ask': float(t.get('ask', 0)),
                'bidQty': float(t.get('bidSize', 0)),
                'askQty': float(t.get('askSize', 0))
            }
        return tickers
