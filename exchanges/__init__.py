from .base import Exchange
from .mexc import MexcExchange
from .binance import BinanceExchange
from .kucoin import KuCoinExchange
from .bybit import BybitExchange
from .htx import HTXExchange

# Factory or registry if needed
def get_exchange(name: str):
    if name.lower() == 'mexc': return MexcExchange()
    if name.lower() == 'binance': return BinanceExchange()
    if name.lower() == 'kucoin': return KuCoinExchange()
    if name.lower() == 'bybit': return BybitExchange()
    if name.lower() in ['htx', 'huobi']: return HTXExchange()
    return None
