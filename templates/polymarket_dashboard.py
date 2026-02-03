# Backend: FastAPI + OpenClaw integration

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from py_clob_client import ClobClient
import os

# Configurar API key via Render Secrets
API_KEY = os.getenv("POLY_API_KEY")
BASE_URL = "https://api.polymarket.com"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar cliente OpenClaw/Polymarket
class Market(BaseModel):
    market_id: str
    name: str
    options: list

class BetRequest(BaseModel):
    market_id: str
    option: str
    amount: float

l1 = ClobClient(private_key=API_KEY)

@app.on_event("startup")
async def startup():
    try:
        await l1.derive_api_key()
        print("✅ Conectado ao Polymarket com sucesso")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        raise e

@app.get("/api/markets")
async def get_markets():
    # Exemplo fictício, substituir por fetch real da API Polymarket
    return [
        {"market_id": "1", "name": "Quem ganha o jogo A?", "options": ["Time X", "Time Y"]},
        {"market_id": "2", "name": "Resultado do evento B?", "options": ["Sim", "Não"]}
    ]

@app.post("/api/bet")
async def place_bet(bet: BetRequest):
    try:
        # Aqui você chamaria o método OpenClaw ou py_clob_client para apostar
        # Ex: await l1.place_order(market_id=bet.market_id, option=bet.option, amount=bet.amount)
        print(f"Aposta enviada: {bet.market_id}, {bet.option}, {bet.amount}")
        return {"status": "success", "message": "Aposta enviada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
