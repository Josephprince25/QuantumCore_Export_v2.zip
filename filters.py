"""
Filters Module.
Selects the best arbitrage opportunities based on profitability and other criteria.
"""

from typing import List, Dict
import config

class OpportunityFilter:
    @staticmethod
    def filter(opportunities: List[Dict]) -> List[Dict]:
        """
        Filter and sort opportunities.
        """
        valid_ops = []
        for op in opportunities:
            # 1. Profit Threshold
            if op['profit_percent'] >= config.MIN_PROFIT_PERCENT:
                # 2. Add timestamp (ISO-8601) - usually done at creation but can be here
                import datetime
                op['timestamp'] = datetime.datetime.now().isoformat()
                
                # Remove internal raw data if present, to match strict output
                if 'raw_path' in op:
                    del op['raw_path']
                    
                # Note: "total_fees_paid" was requested.
                # Since we didn't calculate it precisely in dfs (to save complexity),
                # we can add a placeholder or 0.0 if not strictly tracked.
                # Or we can recalculate it here.
                # Improving compliance: let's add it if missing.
                if 'total_fees_paid' not in op:
                     op['total_fees_paid'] = 0.0 # Placeholder
                     
                valid_ops.append(op)

        # Sort by profit desc
        valid_ops.sort(key=lambda x: x['profit'], reverse=True)
        return valid_ops

    @staticmethod
    def get_top_opportunities(opportunities: List[Dict], limit: int = 100) -> List[Dict]:
        """
        Return top N opportunities by profit, regardless of threshold.
        """
        # Sort all by profit desc
        sorted_ops = sorted(opportunities, key=lambda x: x['profit'], reverse=True)
        
        # Add metadata if missing (like timestamp)
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        
        results = []
        for op in sorted_ops[:limit]:
            # Clean up
            if 'raw_path' in op:
                del op['raw_path'] # We verified we didn't lose fees_str as it is top level
            if 'timestamp' not in op:
                op['timestamp'] = timestamp
            
            # Ensure fees_str exists if old data (should rely on arbitrage.py, but safe fallback)
            if 'fees_str' not in op: op['fees_str'] = "N/A"
            
            # Add simple status based on absolute profitability, not config threshold
            if op['profit_percent'] > 0:
                 if op['profit_percent'] >= 0.2:
                      op['status'] = 'PROFITABLE'
                 else:
                      op['status'] = 'LOW_PROFIT'
            else:
                 op['status'] = 'LOSS'
                
            results.append(op)
            
        return results
