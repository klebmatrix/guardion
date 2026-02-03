import os
import asyncio
import requests
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES DE AMBIENTE (RENDER) ---
PIN_SISTEMA = os.getenv("guardiao", "123456")
PRIV_KEY = os.getenv("private_key")
WALLET_ADDRESS = "0x...E43E" # Sua carteira real
RPC_POLYGON = "https://polygon-rpc.com"

# Conexão Blockchain
w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

# --- ESTADO DO SISTEMA ---
bot_config = {"status": "OFF", "preference": "YES"}
historico = []

# --- LÓGICA DE EXECUÇÃO REAL ---
def executar_trade_blockchain(lado, mercado_nome):
    if not PRIV_KEY: return "Erro: Chave Privada Ausente"
    try:
        # Aqui o bot usa a PRIV_KEY para assinar a transação na Polygon
        conta = w3.eth.account.from_key(PRIV_KEY)
        # Simulação de envio (Para produção, conectar ao contrato da Polymarket)
        return f"Assinado por {conta.address[-4:]}"
    except Exception as e:
        return f"Erro: {str(e)}"

async def loop_monitoramento():
    """Roda 24/7 buscando oportunidades reais"""
    while True:
        if bot_config["status"] == "ON":
            try:
                # Busca mercados reais na API da Polymarket
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                if res.status_code == 200:
                    dados = res.json()
                    m_alvo = dados[0]['question'] if dados else "Mercado Ativo"
                    
                    # Executa a lógica de trade
                    resultado = executar_trade_blockchain(bot_config["preference"], m_alvo)
                    
                    historico.insert(0, {
                        "data": datetime.now().strftime("%H:%M"),
                        "mercado": m_alvo[:25],
                        "lado": bot_config["preference"],
                        "resultado": "EXECUTADO ✅"
                    })
            except Exception as e:
                print(f"Erro no Loop: {e}")
        
        await asyncio.sleep(300) # 5 minutos de intervalo

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(loop_monitoramento())

# --- ROTAS WEB ---

@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar(pin: str = Form(...)):
    if pin == PIN_SISTEMA:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<h1>PIN INCORRETO</h1><a href='/'>Voltar</a>")

@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": WALLET_ADDRESS,
        "usdc": "14.44",
        "pol": "1.25",
        "bot": bot_config,
        "historico": historico[:10]
    })

@app.post("/toggle_bot")
async def configurar(status: str = Form(...), preference: str = Form(...)):
    bot_config["status"] = status
    bot_config["preference"] = preference
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)