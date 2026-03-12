import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from core.pheromone_engine import PheromoneEngine
from nodes.scouts import BinanceScout
from nodes.queen import QueenNode

engine = PheromoneEngine()
scout = BinanceScout(engine)
queen = QueenNode(engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    asyncio.create_task(engine.decay_loop())
    asyncio.create_task(scout.run())
    asyncio.create_task(queen.run())

@app.get("/")
async def root(): return FileResponse("static/index.html")

@app.get("/bias/bull")
async def force_bull():
    await engine.update_trend("BULLISH", manual=True)
    await engine.add_pheromone(100.0, "Manual-Override", "BULL")
    return {"status": "Bullish Bias Forced"}

@app.get("/bias/bear")
async def force_bear():
    await engine.update_trend("BEARISH", manual=True)
    await engine.add_pheromone(100.0, "Manual-Override", "BEAR")
    return {"status": "Bearish Bias Forced"}

@app.get("/bias/reset")
async def reset_bias():
    async with engine.lock: engine.manual_bias = False
    return {"status": "Manual Bias Released"}

@app.get("/portfolio/reset")
async def reset_portfolio():
    await queen.reset_portfolio()
    return {"status": "Portfolio Reset to $20.00"}

@app.websocket("/ws/swarm")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            state = await engine.get_state()
            q = await queen.get_data()
            payload = {
                "portfolio": q["balance"],
                "bias": state["bias"],
                "bull": state["bull"],
                "bear": state["bear"],
                "prices": state["prices"],
                "active_trades": q["trades"],
                "stats": {"win_rate": q["wr"], "wins": q["wins"], "losses": q["losses"]}
            }
            await websocket.send_json(payload)
            await asyncio.sleep(0.5)
        except: break