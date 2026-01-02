"""
Main Orchestrator.
Iterates over selected exchanges and runs arbitrage search.
"""

import sys
import json
import logging
from typing import Dict, List
import concurrent.futures

from exchanges import get_exchange
from market_data import MarketData
from graph import MarketGraph
from arbitrage import ArbitrageEngine
from filters import OpportunityFilter
import config

# Configure logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_exchange(exchange_name: str) -> Dict:
    """
    Run full analysis for a single exchange.
    """
    logger.info(f"Starting analysis for {exchange_name}...")
    
    # 1. Init Exchange
    exchange = get_exchange(exchange_name)
    if not exchange:
        logger.error(f"Unknown exchange: {exchange_name}")
        return {"profitable": [], "all_paths": []}

    # 2. Fetch Data
    market_data = MarketData(exchange)
    market_data.update_data()
    valid_pairs = market_data.get_valid_pairs()
    
    if not valid_pairs:
        logger.warning(f"[{exchange_name}] No valid pairs found.")
        return {"profitable": [], "all_paths": []}

    # 3. Build Graph
    graph = MarketGraph()
    graph.build(valid_pairs)

    # 4. Search Arbitrage
    engine = ArbitrageEngine(graph)
    opportunities = engine.find_arbitrage()
    
    # 5. Filter
    profitable_ops = OpportunityFilter.filter(opportunities)
    top_ops = OpportunityFilter.get_top_opportunities(opportunities, limit=50)

    # Tag with exchange name
    for op in profitable_ops: op['exchange'] = exchange_name
    for op in top_ops: op['exchange'] = exchange_name

    logger.info(f"[{exchange_name}] Analysis complete. Profitable: {len(profitable_ops)}")
    
    return {
        "profitable": profitable_ops,
        "all_paths": top_ops
    }

def run_analysis(target_exchanges: List[str] = None) -> Dict:
    """
    Run analysis for multiple exchanges (parallel or sequential).
    """
    if target_exchanges is None:
        target_exchanges = config.ENABLED_EXCHANGES

    combined_profitable = []
    combined_all = []

    # Run in parallel using Processes to bypass GIL for CPU-heavy tasks
    # Max workers limited to cpu_count or number of exchanges
    import os
    max_workers = min(len(target_exchanges), os.cpu_count() or 4)
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_exch = {executor.submit(analyze_exchange, name): name for name in target_exchanges}
        for future in concurrent.futures.as_completed(future_to_exch):
            name = future_to_exch[future]
            try:
                data = future.result(timeout=120) # Extinct timeout
                if data:
                    combined_profitable.extend(data.get("profitable", []))
                    combined_all.extend(data.get("all_paths", []))
            except Exception as e:
                logger.error(f"[{name}] CRITICAL FAILURE or TIMEOUT: {e}")

    # Sort combined results
    combined_profitable.sort(key=lambda x: x['profit'], reverse=True)
    combined_all.sort(key=lambda x: x['profit'], reverse=True)

    return {
        "profitable": combined_profitable,
        "all_paths": combined_all[:100] # Global top 100
    }

if __name__ == "__main__":
    # Test run
    results = run_analysis(['MEXC', 'Binance'])
    print(json.dumps(results['profitable'], indent=2))
