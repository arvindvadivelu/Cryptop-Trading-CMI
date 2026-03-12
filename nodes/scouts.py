import asyncio
import json
import logging
import websockets
from core.pheromone_engine import PheromoneEngine

logger = logging.getLogger("CMI.Scouts")

class BinanceScout:
    def __init__(self, engine: PheromoneEngine):
        self.engine = engine
        self.ws_url = "wss://dstream.binance.com/ws/btcusd_perp@kline_5m/btcusd_perp@kline_1h"
        self.candles_5m = []
        self.candles_1h = []

    async def run(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    logger.info("[Scout] Connected to BTCUSD Real-Time Stream")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        k = data['k']
                        t_frame = k['i']
                        is_closed = k['x']
                        price = float(k['c'])
                        
                        if t_frame == '5m':
                            async with self.engine.lock:
                                self.engine.latest_prices["btcusd"] = price
                            if is_closed:
                                self.candles_5m.append(k)
                                if len(self.candles_5m) > 5: self.candles_5m.pop(0)
                                await self._check_5m_trigger(price)
                        
                        if t_frame == '1h' and is_closed:
                            self.candles_1h.append(k)
                            await self._update_h1_bias()
            except Exception as e:
                logger.error(f"[Scout] Connection Error: {e}. Reconnecting...")
                await asyncio.sleep(5)

    async def _update_h1_bias(self):
        if len(self.candles_1h) < 2: return
        last = self.candles_1h[-1]
        bias = "BULLISH" if float(last['c']) > float(last['o']) else "BEARISH"
        await self.engine.update_trend(bias)

    async def _check_5m_trigger(self, price):
        if len(self.candles_5m) < 3: return
        state = await self.engine.get_state()
        c = self.candles_5m[-1]
        
        # Sniper Entry: Displacement in direction of H1 Trend
        if state["bias"] == "BULLISH" and float(c['c']) > float(c['h']):
            await self.engine.add_pheromone(90.0, "Sniper-5M", "BULL")
        elif state["bias"] == "BEARISH" and float(c['c']) < float(c['l']):
            await self.engine.add_pheromone(90.0, "Sniper-5M", "BEAR")