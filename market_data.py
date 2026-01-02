"""
Market Data Module.
Generic processor for any Exchange.
"""

import logging
from typing import List, Dict
from exchanges.base import Exchange

logger = logging.getLogger(__name__)

class MarketData:
    def __init__(self, exchange: Exchange):
        self.exchange = exchange
        self.valid_pairs = []

    def update_data(self):
        """
        Fetch info and tickers, merge them, and store valid pairs.
        """
        # Implement Caching for Symbols (Static Data)
        import os
        import json
        import time
        
        cache_file = f"cache_symbols_{self.exchange.name}.json"
        symbols = []
        loaded_from_cache = False
        
        if os.path.exists(cache_file):
            # Check age (1 hour = 3600 seconds)
            if time.time() - os.path.getmtime(cache_file) < 3600:
                try:
                    with open(cache_file, 'r') as f:
                        symbols = json.load(f)
                    loaded_from_cache = True
                    logger.info(f"[{self.exchange.name}] Loaded {len(symbols)} symbols from cache.")
                except:
                    pass
        
        if not loaded_from_cache:
            logger.info(f"[{self.exchange.name}] Fetching symbols (Live)...")
            symbols = self.exchange.fetch_symbols()
            if symbols:
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(symbols, f)
                except Exception as e:
                    logger.error(f"Failed to cache symbols: {e}")
        
        logger.info(f"[{self.exchange.name}] Fetching tickers...")
        tickers = self.exchange.fetch_tickers()
        
        if not symbols or not tickers:
            logger.error(f"[{self.exchange.name}] Failed to fetch data.")
            self.valid_pairs = []
            return

        self.valid_pairs = []
        for s in symbols:
            sym = s['symbol']
            
            # Match symbol to ticker (handle potential casing issues)
            # Some APIs use lowercase, generic tickers usually match symbol string
            ticker = tickers.get(sym)
            if not ticker:
                 # Try variations if needed, e.g. removal of hyphens or casing
                 # For now assume exact match or simple case match
                 ticker = tickers.get(sym.upper()) or tickers.get(sym.lower())

            if ticker:
                if ticker['bid'] > 0 and ticker['ask'] > 0:
                    merged = s.copy()
                    merged.update(ticker)
                    self.valid_pairs.append(merged)
        
        logger.info(f"[{self.exchange.name}] Data updated. Valid pairs: {len(self.valid_pairs)}")

    def get_valid_pairs(self) -> List[Dict]:
        return self.valid_pairs
