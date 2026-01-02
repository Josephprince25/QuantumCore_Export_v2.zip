"""
Graph Module.
Builds the market graph from validated market data.
"""

from typing import List, Dict

class MarketGraph:
    def __init__(self):
        self.adj = {}

    def build(self, valid_pairs: List[Dict]):
        """
        Construct the directed graph.
        
        Uses 'fee_taker' from the pair data for edges.
        """
        self.adj = {}

        for p in valid_pairs:
            try:
                base = p['base']
                quote = p['quote']
                symbol = p['symbol']
            except KeyError as e:
                print(f"ERROR in Graph Build: Missing key {e} in pair: {p}")
                continue
            
            # Default to taker fee as per prompt
            fee = p.get('fee_taker', 0.001)
            
            bid = p['bid']
            ask = p['ask']

            # Ensure uppercase node names/currencies
            base = base.upper()
            quote = quote.upper()

            if base not in self.adj: self.adj[base] = []
            if quote not in self.adj: self.adj[quote] = []

            # Edge 1: Quote -> Base (BUY at ASK)
            # You have Quote, want Base.
            if ask > 0:
                self.adj[quote].append({
                    'to': base,
                    'symbol': symbol,
                    'action': 'BUY',
                    'price': ask,
                    'fee': fee
                })

            # Edge 2: Base -> Quote (SELL at BID)
            # You have Base, want Quote.
            if bid > 0:
                self.adj[base].append({
                    'to': quote,
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': bid,
                    'fee': fee
                })
    
    def get_neighbors(self, coin: str) -> List[Dict]:
        return self.adj.get(coin, [])
