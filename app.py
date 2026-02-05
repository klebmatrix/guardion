import os, asyncio, json, uvicorn, httpx
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONEXÃO ---
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PRIV_KEY = os.getenv("private_key", "").strip()
if PRIV_KEY and not PRIV_KEY.startswith("0x"): PRIV_KEY = "0x" + PRIV_KEY

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
# O Azuro usa o Proxy Front de apostas
AZURO_PROXY = "0x204407BB66603386C959440478a149744c7d70f9" 

w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# Estratégia: Apostar apenas em Favoritos (Odds baixas = Alta probabilidade)
bot_config = {
    "status": "OFF",
    "min_odds": 1.20, # Equivalente a $0.80 na Polymarket
    "max_odds": 1.90, # Equivalente a $0.52 na Polymarket
    "esportes": ["Football", "Basketball", "Tennis"]
}

def registrar_log(msg, lado="AZURO", res="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, {"data": agora, "mercado": msg, "lado": lado, "resultado": res})
        with open("logs.json", "w") as f: json.dump(dados[:30], f)
    except: pass

# --- MOTOR DE BUSCA ESPORTIVA ---
async def sniper_esportivo():
    while True:
        if bot_config["status"] == "ON":
            try:
                # Usando o indexador do Azuro para buscar jogos ativos na Polygon
                query = """
                {
                  games(where: { status: "Active", hasActiveConditions: true }, first: 20, orderBy: turnover, orderDirection: desc) {
                    id
                    league { name }
                    sport { name }
                    participants { name }
                    conditions {
                      id
                      outcomes { id currentOdds }
                    }
                  }
                }
                """
                async with httpx.AsyncClient() as client:
                    # Endpoint do subgrafo Azuro
                    res = await client.post("https://thegraph.com/explorer/subgraph/azuro-protocol/azuro-api-polygon-v2", json={'query': query})
                    
                    if res.status_code == 200:
                        jogos = res.json().get('data', {}).get('games', [])
                        for jogo in jogos:
                            sport = jogo['sport']['name']
                            if sport in bot_config["esportes"]:
                                participants = [p['name'] for p in jogo['participants']]
                                cond = jogo['conditions'][0]
                                
                                for outcome in cond['outcomes']:
                                    odd = float(outcome['currentOdds'])
                                    
                                    # Se a odd for de favorito dentro do nosso range
                                    if bot_config["min_odds"] <= odd <= bot_config["max_odds"]:
                                        match_name = f"{participants[0]} vs {participants[1]}"
                                        registrar_log(f"OPORTUNIDADE: {match_name} @ {odd}", "ESPORTE", "ANALISADO")
                                        
                                        # Aqui entraria a função de aposta (Contract Call)
                                        # Por segurança, vamos apenas monitorar no primeiro ciclo
                                        break
                
            except Exception as e:
                print(f"Erro Azuro: {e}")
                
        await asyncio.sleep(15)

# --- (As outras rotas de Dashboard e Login permanecem as mesmas) ---

@app.on_event("startup")
async def startup_event():
    if not os.path.exists("logs.json"):
        with open("logs.json", "w") as f: json.dump([], f)
    asyncio.create_task(sniper_esportivo())

# ... (Mantenha o restante do código do Dashboard anterior)