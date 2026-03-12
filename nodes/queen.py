import asyncio
import logging
from core.pheromone_engine import PheromoneEngine

logger = logging.getLogger("CMI.Queen")

class QueenNode:
    def __init__(self, engine: PheromoneEngine):
        self.engine = engine
        self.balance = 20.00
        self.open_trades = []
        self.wins, self.losses = 0, 0

    async def reset_portfolio(self):
        self.balance = 20.00
        self.wins = 0
        self.losses = 0
        self.open_trades = []
        logger.warning("👑 PORTFOLIO RESET TO $20.00")

    async def run(self):
        while True:
            await asyncio.sleep(0.5)
            state = await self.engine.get_state()
            price = state["prices"].get("btcusd", 0)
            if price == 0: continue

            await self._monitor(price)

            if len(self.open_trades) == 0:
                if state["bull"] > 85 and state["bias"] == "BULLISH":
                    await self._entry("LONG", price)
                elif state["bear"] > 85 and state["bias"] == "BEARISH":
                    await self._entry("SHORT", price)

    async def _entry(self, side, price):
        risk = price * 0.005 # 0.5% Stop Loss
        sl = price - risk if side == "LONG" else price + risk
        tp = price + (risk * 3) if side == "LONG" else price - (risk * 3)
        
        self.open_trades.append({"direction": side, "entry": price, "sl": sl, "tp": tp, "size": self.balance})
        logger.warning(f"🎯 SNIPER {side} @ {price} | TP: {tp}")

    async def _monitor(self, price):
        for t in self.open_trades[:]:
            win = (t['direction'] == "LONG" and price >= t['tp']) or (t['direction'] == "SHORT" and price <= t['tp'])
            loss = (t['direction'] == "LONG" and price <= t['sl']) or (t['direction'] == "SHORT" and price >= t['sl'])
            
            if win or loss:
                # Realize 100% account profit/loss
                pnl_mult = 0.015 if win else -0.005
                self.balance += (t['size'] * pnl_mult)
                if win: self.wins += 1 
                else: self.losses += 1
                self.open_trades.remove(t)

    async def get_data(self):
        total = self.wins + self.losses
        wr = (self.wins / total * 100) if total > 0 else 0
        return {"balance": self.balance, "trades": self.open_trades, "wr": wr, "wins": self.wins, "losses": self.losses}