"""
Arbitrage Engine Module.
Implements the DFS algorithm to find profitable paths.
"""

from typing import List, Dict, Set
import config
from simulator import Simulator
from graph import MarketGraph

class ArbitrageEngine:
    def __init__(self, graph: MarketGraph):
        self.graph = graph
        self.opportunities = []

    def find_arbitrage(self) -> List[Dict]:
        """
        Run DFS from each stablecoin to find opportunities.
        """
        self.opportunities = []
        
        for start_coin in config.STABLECOINS:
            # Only start if the coin exists in the graph
            if start_coin in self.graph.adj:
                self._dfs(
                    start_coin=start_coin,
                    current_coin=start_coin,
                    current_amount=config.START_AMOUNT,
                    path=[],
                    visited={start_coin}
                )
        
        return self.opportunities

    def _dfs(self, start_coin: str, current_coin: str, current_amount: float, path: List[Dict], visited: Set[str]):
        """
        Depth First Search to explore trading paths.
        """
        depth = len(path)

        # Stop conditions
        if depth > config.MAX_DEPTH:
            return

        # Check for cycle completion (Arbitrage found)
        # We must have at least MIN_TRADES and returned to start_coin
        if current_coin == start_coin and depth >= config.MIN_TRADES:
            self._record_opportunity(start_coin, current_amount, path)
            return

        # If we are at a stablecoin but it's NOT the start_coin, and we are deep enough, 
        # we might treat it as an end? 
        # Prompt says: "Arbitrage cycle must start and end with a stablecoin". 
        # Usually implies the SAME stablecoin for triangular arb.
        # "Start & end coin must be stablecoin" -> usually separate? 
        # But "Profit" defined as "Final amount > starting amount" implies comparison 
        # which is easiest if same coin.
        # Example prompt: "USDT -> TRX -> BTC -> USDT". Same coin.
        # So we only close loop on start_coin.

        # If we reached a different stablecoin, we could technically swap it back to start_coin 
        # but that would be an extra step (covered by recursion naturally if edges exist).
        # We simply continue.

        # Iterate neighbors
        neighbors = self.graph.get_neighbors(current_coin)
        for edge in neighbors:
            next_coin = edge['to']

            # Constraint: No coin repetition inside path
            # visited set includes start_coin.
            # If next_coin is start_coin, it's allowed (closing the loop).
            # If next_coin is visited and NOT start_coin, skip.
            if next_coin in visited and next_coin != start_coin:
                continue

            # Early pruning: If amounts become trivial (near 0), stop.
            if current_amount < 0.00000001:
                continue

            # Simulate execution
            next_amount = Simulator.simulate_trade(
                amount_in=current_amount,
                price=edge['price'],
                fee_rate=edge['fee'],
                is_buy=(edge['action'] == 'BUY')
            )

            # Recurse
            # Add next_coin to visited for the next step
            # Note: We create new sets/lists to avoid mutation issues in recursion
            new_path = path + [{
                'symbol': edge['symbol'],
                'fee': edge['fee'],
                'action': edge['action'],
                'from': current_coin,
                'to': next_coin,
                'price': edge['price'],
                'input': current_amount,
                'output': next_amount
            }]
            
            self._dfs(
                start_coin=start_coin,
                current_coin=next_coin,
                current_amount=next_amount,
                path=new_path,
                visited=visited | {next_coin}
            )

    def _record_opportunity(self, start_coin: str, end_amount: float, path: List[Dict]):
        """
        Format and store the found opportunity.
        """
        profit = end_amount - config.START_AMOUNT
        profit_percent = (profit / config.START_AMOUNT) * 100

        # Construct path string
        # "USDT -> TRX", "TRX -> BTC", ...
        path_strs = [f"{p['from']} -> {p['to']}" for p in path]
        
        # Calculate fees
        total_fees = 0.0
        fee_details = []
        for p in path:
            # Fee paid in Quote currency usually, but here we estimate in Start Coin terms for simplicity if possible?
            # Or just sum the drops. 
            # Better: Sum (Input_Value_in_Path - Output_Value_in_Price_Before_Fee) ? 
            # Actually simplest is: Fee in output asset terms at that hop. 
            # Let's just track the rates used for display as requested.
            fee_rate = p.get('fee', 0.0)
            fee_details.append(f"{fee_rate*100:.2f}%")
            
            # Approximate value lost in USD/StartCoin terms (rough heuristic)
            # This is hard to normalize without a global price vector. 
            # We will rely on profit diff, but user wants "how much fee".
            # formatting: "0.1%"
        
        # Unique fees used
        unique_fees = list(set(fee_details))
        fees_str = "/".join(unique_fees)
        
        # Detailed breakdown for UI
        fee_breakdown = []
        for p in path:
            fee_breakdown.append({
                "step": f"{p['from']} -> {p['to']}",
                "symbol": p['symbol'],
                "action": p['action'],
                "fee_rate": p['fee'],
                "fee_percent": f"{p['fee']*100:.3f}%"
            })

        op = {
            "start_coin": start_coin,
            "start_amount": config.START_AMOUNT,
            "end_coin": start_coin,
            "end_amount": round(end_amount, 4),
            "profit": round(profit, 4),
            "profit_percent": round(profit_percent, 4),
            "trade_path": path_strs,
            "number_of_trades": len(path),
            "fees_str": fees_str, 
            "fee_breakdown": fee_breakdown, # New field for UI modal
            "raw_path": path
        }
        self.opportunities.append(op)
