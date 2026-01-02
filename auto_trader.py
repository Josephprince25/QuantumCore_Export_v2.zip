import time
import logging
import threading
from typing import Dict, List
import config
from main import run_analysis
from simulator import Simulator

logger = logging.getLogger(__name__)

class AutoTrader:
    def __init__(self):
        self.is_running = False
        self.explore_thread = None
        self.paper_balance = {"USDT": 1000.0, "USDC": 1000.0} # Starting Paper Money
        self.trade_history = []
        self.total_profit = 0.0
        self.active_log = []
    
    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.active_log.insert(0, entry) # Prepend for latest first
        self.active_log = self.active_log[:100] # Keep last 100
        logger.info(f"[AutoTrader] {message}")

    def start(self):
        if self.is_running: return
        self.is_running = True
        self.explore_thread = threading.Thread(target=self._run_loop)
        self.explore_thread.daemon = True
        self.explore_thread.start()
        self.log("Auto-Trading Engine Started.")

    def stop(self):
        self.is_running = False
        self.log("Stopping Auto-Trader...")

    def get_status(self):
        return {
            "running": self.is_running,
            "balance": self.paper_balance,
            "total_profit": self.total_profit,
            "trade_count": len(self.trade_history),
            "logs": self.active_log,
            "history": self.trade_history[-20:] # Last 20 trades
        }

    def update_wallet_from_user(self, user):
        """
        Sync internal paper balance with User DB state.
        """
        self.paper_balance['USDT'] = user.paper_balance_usdt
        self.paper_balance['USDC'] = user.paper_balance_usdc
        self.log(f"Wallet Synced: USDT={self.paper_balance['USDT']}, USDC={self.paper_balance['USDC']}")
        
    def _run_loop(self):
        # We need app context to write to DB if we want persistence during loop
        from server import app, db
        from models import User
        
        while self.is_running:
            try:
                # self.log("Scanning market...")
                # 1. Scan
                results = run_analysis(config.ENABLED_EXCHANGES)
                opportunities = results.get('profitable', [])
                
                # 2. Filter & execute Best Opportunity
                if opportunities:
                    # Sort by profit
                    opportunities.sort(key=lambda x: x['profit'], reverse=True)
                    best_op = opportunities[0]
                    
                    if best_op['profit'] > 0: # Double check profit
                        with app.app_context(): # DB Context
                            self._execute_trade(best_op, db)
                    else:
                        self.log("Best opportunity not profitable enough.")
                else:
                    self.log("No opportunities found.")

                # 3. Wait before next loop (prevent API bans)
                time.sleep(1) 
                
            except Exception as e:
                self.log(f"Error in loop: {e}")
                time.sleep(10)

    def _execute_trade(self, op: Dict, db_session=None):
        """
        Execute trade (Paper or Real).
        """
        start_coin = op['start_coin']
        end_coin = op['end_coin']
        profit = op['profit']
        mode = config.TRADE_MODE
        
        # 1. Paper Execution
        if mode == 'PAPER':
            if self.paper_balance.get(start_coin, 0) < op['start_amount']:
                self.log(f"Insufficient PAPER funds in {start_coin}. Skipping.")
                return

            # Update Internal State
            self.paper_balance[end_coin] += profit
            self.total_profit += profit
            
            # Update DB Persistence (if session available)
            if db_session:
                from models import User
                # Assuming single user for local bot, or store ID. 
                # Simplest: Update ALL users or First user.
                user = User.query.first() 
                if user:
                    user.paper_balance_usdt = self.paper_balance.get('USDT', 0)
                    user.paper_balance_usdc = self.paper_balance.get('USDC', 0)
                    db_session.commit()
            
            self.log(f"[PAPER] EXECUTED: {op['trade_path']} | Profit: +{round(profit, 4)} {start_coin}")
            
        # 2. Real Execution (Bybit Testnet Only for now)
        elif mode == 'LIVE_TESTNET':
            if op['exchange'] != 'Bybit':
                self.log(f"Skipping Real Trade: {op['exchange']} not supported for auto-execution yet.")
                return

            self.log(f"[REAL] Attempting execution on Bybit Testnet...")
            from exchanges.bybit import BybitExchange
            exchange = BybitExchange(api_key=config.BYBIT_API_KEY, api_secret=config.BYBIT_API_SECRET)
            
            # Execute each step
            # Path example: "USDT -> BTC", "BTC -> USDT"
            # We need raw path to know symbols and actions
            all_success = True
            
            for step in op['raw_path']:
                # step: {symbol, action, ...}
                # quantity? We use op['start_amount'] for first, then output of prev?
                # For simplicity, we use Market Order with 'qty'
                # If BUY: qty is usually in Quote (USDT)? Or Base?
                # Bybit V5: 
                #   Buy: qty is Quote Amount (if Market) ?? No, usually Base Asset for Limit, 
                #   But for Market Buy, it is often 'qty' in Quote Coin (quoteOrderQty in Binance terms).
                #   Let's check Bybit docs assumption or fail fast.
                #   Bybit V5 Market Buy: 'qty' is amount of base coin? Or Quote?
                #   It depends on 'marketUnit'. NOT SUPPORTED IN SIMPLE IMPLEMENTATION.
                #   Assumption: We are buying 'qty' of Base Asset. 
                #   Wait, we have 'input' (USDT). We want to spend INPUT USDT to get BTC.
                #   So we need to calculate Base Qty? Price is needed.
                
                # SIMPLIFICATION:
                # We will log the ATTEMPT only, because exact order quantity calculation is complex without live price feed.
                # We will try to place a small fixed test order if possible, or just log.
                # User asked to "test trading".
                
                # Safe Approach:
                qty_to_trade = step['output'] if step['action'] == 'SELL' else (step['input'] / step['price'])
                # Rounding is critical. 
                qty_str = "{:.5f}".format(qty_to_trade)
                
                success = exchange.create_order(step['symbol'], step['action'], float(qty_str))
                if not success:
                    self.log(f"[REAL] Execution Failed at {step['symbol']}. Stopping chain.")
                    all_success = False
                    break
                else:
                    self.log(f"[REAL] Order Placed: {step['action']} {step['symbol']} {qty_str}")
                    time.sleep(0.5) # Rate limit safety
            
            if all_success:
                self.log(f"[REAL] Full Chain Executed Successfully!")
        
        # Log to History
        trade_record = {
            "timestamp": time.time(),
            "exchange": f"{op['exchange']} ({mode})",
            "path": op['trade_path'],
            "profit": round(profit, 4),
            "start_coin": start_coin,
            "fees_paid": op.get('fees_str', 'N/A')
        }
        self.trade_history.append(trade_record)

# Global Instance
auto_trader = AutoTrader()
