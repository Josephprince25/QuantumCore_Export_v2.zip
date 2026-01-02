"""
Trade Simulator Module.
Handles the math for price conversion and fee deduction.
"""

class Simulator:
    @staticmethod
    def simulate_trade(amount_in: float, price: float, fee_rate: float, is_buy: bool) -> float:
        """
        Calculate amount_out based on input, price, and fee.
        
        BUY (Quote -> Base):
          amount_out = amount_in / ask_price
          amount_out -= amount_out * fee
          
        SELL (Base -> Quote):
          amount_out = amount_in * bid_price
          amount_out -= amount_out * fee
        """
        if is_buy:
            # We have Quote, we want Base.
            # Price is Quote per Base (Ask).
            # Raw Base = Amount Quote / Price
            amount_out = amount_in / price
        else:
            # We have Base, we want Quote.
            # Price is Quote per Base (Bid).
            # Raw Quote = Amount Base * Price
            amount_out = amount_in * price

        # Deduct Fee
        amount_out_after_fee = amount_out * (1 - fee_rate)
        return amount_out_after_fee
