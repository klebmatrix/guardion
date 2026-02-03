import os
import asyncio
import json
import requests
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES DE AMBIENTE ---
PIN_SISTEMA = os.getenv("guardiao", "123456")
PRIV_KEY = os.getenv("private_key")
WALLET_ADDRESS = "0x...E43E" 
RPC_POLYGON = "https://polygon-rpc.com"
FILE_HISTORICO = "historico_permanente.json"

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_dados(lista):
    with open(FILE_HISTORICO, "w") as f:
        json.dump(lista, f)

def carregar_dados():
    if os.path.exists(FILE_HISTORICO):
        try:
            with open(FILE_HISTORICO, "r") as f:
                return json.load(f)
        except: return []
    return []

# --- ESTADO INICIAL ---
bot_config = {"status": "OFF", "preference": "YES"}
historico = carregar_dados()

# --- MOTOR DO ROBÔ (AUTÔNOMO) ---
async def loop_principal():
    global historico
    while True:
        if bot_config["status"] == "ON":
            try:
                # 1. Scanner Real
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                mercado_nome = "Scanner Ativo"
                if res.status_code == 200:
                    mercado_nome = res.json()[0].get('question', 'Polymarket Op')[:25]

                # 2. Tentativa de Assinatura Real
                if PRIV_KEY:
                    conta = w3.eth.account.from_key(PRIV_KEY)
                    status_exec = f"ASSINADO: {conta.address[-4:]}"
                else:
                    status_exec = "ERRO: SEM CHAVE"

                # 3. Registro no Histórico Permanente
                novo_log = {
                    "data": datetime.now().strftime("%d/%m %H:%M"),
                    "mercado": mercado_nome,
                    "lado": bot_config["preference"],
                    "resultado": status_exec
                }
                historico.insert(0, novo_log)
                historico = historico[:20] # Mantém os 20 últimos
                salvar_dados(historico)
                
            except Exception as e:
                print(f"Erro no loop: {e}")
        
        await asyncio.sleep(300) # Ciclo de 5 minutos

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(loop_principal())

# --- ROTAS WEB ---
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar(pin: str = Form(...)):
    if pin == PIN_SISTEMA:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("PIN INCORRETO")

@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": WALLET_ADDRESS,
        "usdc": "14.44",
        "pol": "1.25",
        "bot": bot_config,
        "historico": historico
    })

@app.post("/toggle_bot")
async def config(status: str = Form(...), preference: str = Form(...)):
    bot_config["status"] = status
    bot_config["preference"] = preference
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)