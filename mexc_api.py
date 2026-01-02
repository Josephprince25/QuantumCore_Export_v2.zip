"""
MEXC API Interaction Module.
Handles fetching of exchange info and market data.
"""

import requests
import logging
from typing import Dict, List, Any
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MexcApi:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.session = requests.Session()

    def _get(self, endpoint: str, params: Dict = None) -> Any:
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request Failed: {e}")
            return None

    def fetch_exchange_info(self) -> Dict:
        """
        Fetch exchange rules, symbol information, and filters.
        GET /api/v3/exchangeInfo
        """
        logger.info("Fetching exchange info...")
        return self._get("/api/v3/exchangeInfo")

    def fetch_ticker_book(self) -> List[Dict]:
        """
        Fetch best bid/ask price for all symbols.
        GET /api/v3/ticker/bookTicker
        """
        logger.info("Fetching book tickers...")
        return self._get("/api/v3/ticker/bookTicker")
    
    def fetch_ticker_24hr(self) -> List[Dict]:
        """
        Fetch 24hr ticker for volume data.
        GET /api/v3/ticker/24hr
        """
        logger.info("Fetching 24hr tickers...")
        return self._get("/api/v3/ticker/24hr")
