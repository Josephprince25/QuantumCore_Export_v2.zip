"""
Base Exchange Interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Exchange(ABC):
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url

    @abstractmethod
    def fetch_symbols(self) -> List[Dict]:
        """
        Fetch active spot trading pairs.
        Returns list of dicts:
        {
            'symbol': str,
            'base': str,
            'quote': str,
            'fee_maker': float,
            'fee_taker': float,
            'min_base': float,
            'min_quote': float,
            'filters': dict
        }
        """
        pass

    @abstractmethod
    def fetch_tickers(self) -> Dict[str, Dict]:
        """
        Fetch current bid/ask prices.
        Returns dict:
        {
            'SYMBOL': {'bid': float, 'ask': float, 'bidQty': float, 'askQty': float}
        }
        """
        pass

    def safe_float(self, value, default=0.0):
        if value is None: return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
