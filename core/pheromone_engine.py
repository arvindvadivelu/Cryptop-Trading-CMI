import asyncio
import logging

logger = logging.getLogger("CMI.Engine")

class PheromoneEngine:
    def __init__(self):
        self.bull_score = 0.0
        self.bear_score = 0.0
        self.trend_bias = "NEUTRAL"
        self.manual_bias = False 
        self.latest_prices = {"btcusd": 0.0}
        self.lock = asyncio.Lock()
        self.decay_rate = 0.02 

    async def update_trend(self, bias: str, manual: bool = False):
        async with self.lock:
            if self.manual_bias and not manual:
                return 
            self.trend_bias = bias
            self.manual_bias = manual
            logger.info(f"[TrendNode] Bias set to {bias} (Manual: {manual})")

    async def add_pheromone(self, amount: float, source: str, direction: str):
        async with self.lock:
            if direction == "BULL":
                self.bull_score = min(100.0, self.bull_score + amount)
            else:
                self.bear_score = min(100.0, self.bear_score + amount)

    async def decay_loop(self):
        while True:
            await asyncio.sleep(1)
            async with self.lock:
                self.bull_score = max(0.0, self.bull_score - (self.bull_score * self.decay_rate))
                self.bear_score = max(0.0, self.bear_score - (self.bear_score * self.decay_rate))

    async def get_state(self):
        async with self.lock:
            return {
                "bull": self.bull_score,
                "bear": self.bear_score,
                "bias": self.trend_bias,
                "manual": self.manual_bias,
                "prices": self.latest_prices
            }