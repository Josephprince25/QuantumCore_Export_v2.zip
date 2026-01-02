"""
Bybit Exchange Implementation.
"""
import requests
import logging
from typing import List, Dict
from .base import Exchange

logger = logging.getLogger(__name__)

class BybitExchange(Exchange):
    def __init__(self, api_key=None, api_secret=None):
        super().__init__('Bybit', 'https://api-testnet.bybit.com') # Default to Testnet for safety as per request
        self.session = requests.Session()
        self.api_key = api_key
        self.api_secret = api_secret
        
    def _sign(self, params):
        import time
        import hmac
        import hashlib
        
        timestamp = str(int(time.time() * 1000))
        recv_window = str(5000)
        param_str = str(params) # Use JSON dump for POST or query for GET
        
        # Simple signature: timestamp + key + recv_window + params
        # But for V5, it is:
        # timestamp + key + recv_window + (queryString or jsonBody)
        # We will use this simply for POST (JSON body)
        
        return timestamp, recv_window

    def create_order(self, symbol: str, side: str, qty: float):
        """
        Execute a Market Order on Bybit V5 Testnet.
        """
        if not self.api_key or not self.api_secret:
            logger.error("Bybit API Keys missing.")
            return False

        import time
        import hmac
        import hashlib
        import json
        
        url = "https://api-testnet.bybit.com/v5/order/create"
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        
        payload = {
            "category": "spot",
            "symbol": symbol,
            "side": side.capitalize(), # 'Buy' or 'Sell'
            "orderType": "Market",
            "qty": str(qty),
        }
        
        body = json.dumps(payload)
        
        # Signature
        to_sign = timestamp + self.api_key + recv_window + body
        signature = hmac.new(self.api_secret.encode('utf-8'), to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-SIGN": signature,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json"
        }
        
        try:
            resp = self.session.post(url, headers=headers, data=body)
            data = resp.json()
            if data.get('retCode') == 0:
                logger.info(f"Bybit Order Success: {data}")
                return True
            else:
                logger.error(f"Bybit Order Failed: {data}")
                return False
        except Exception as e:
            logger.error(f"Bybit Order Error: {e}")
            return False

    def _get(self, endpoint: str, params: Dict = None):
        try:
             # Hack: Switch base URL to mainnet for data fetching if needed, 
             # but user asked for Testnet trading. 
             # Ideally validation scans mainnet and trades testnet? 
             # Actually, if price data is from mainnet but you trade on testnet, 
             # arbitrage will likely fail (different prices).
             # We should probably use Testnet for EVERYTHING if mode is Testnet.
             # I'll stick to the base_url set in __init__.
            url = f"{self.base_url}{endpoint}"
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Bybit API Error: {e}")
            return None

    def fetch_symbols(self) -> List[Dict]:
        # Bybit V5
        data = self._get("/v5/market/instruments-info", params={'category': 'spot'})
        if not data or data.get('retCode') != 0: return []
        
        symbols = []
        for s in data.get('result', {}).get('list', []):
            if s.get('status') == 'Trading':
                limit_min_base = 0.0
                limit_min_quote = 0.0
                
                if 'lotSizeFilter' in s:
                    limit_min_base = float(s['lotSizeFilter'].get('minOrderQty', 0))
                    limit_min_quote = float(s['lotSizeFilter'].get('minOrderAmt', 0))

                symbols.append({
                    'symbol': s['symbol'],
                    'base': s['baseCoin'],
                    'quote': s['quoteCoin'],
                    'fee_maker': 0.001,
                    'fee_taker': 0.001,
                    'min_base': limit_min_base,
                    'min_quote': limit_min_quote
                })
        return symbols

    def fetch_tickers(self) -> Dict[str, Dict]:
        data = self._get("/v5/market/tickers", params={'category': 'spot'})
        if not data or data.get('retCode') != 0: return {}
        
        tickers = {}
        for t in data.get('result', {}).get('list', []):
            tickers[t['symbol']] = {
                'bid': float(t.get('bid1Price', 0)),
                'ask': float(t.get('ask1Price', 0)),
                'bidQty': float(t.get('bid1Size', 0)),
                'askQty': float(t.get('ask1Size', 0))
            }
        return tickers
