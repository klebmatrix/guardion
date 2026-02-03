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

# --- CONFIGURAÇÕES REAIS ---
PIN_SISTEMA = os.getenv("guardiao", "123456")
PRIV_KEY = os.getenv("private_key")
WALLET_ADDRESS = "0x...E43E" # Substitua pelo seu endereço completo
RPC_POLYGON = "https://polygon-rpc.com"

# Contrato USDC na Polygon para ler saldo real
USDC_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
USDC_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
usdc_instancia = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(USDC_ABI))

# --- PERSISTÊNCIA ---
FILE_HISTORICO = "historico_permanente.json"

def salvar_dados(lista):
    with open(FILE_HISTORICO, "w") as f: json.dump(lista, f)

def carregar_dados():
    if os.path.exists(FILE_HISTORICO):
        try:
            with open(FILE_HISTORICO, "r") as f: return json.load(f)
        except: return []
    return []

bot_config = {"status": "OFF", "preference": "YES"}
historico = carregar_dados()

# --- MOTOR AUTÔNOMO ---
async def loop_principal():
    global historico
    while True:
        if bot_config["status"] == "ON":
            try:
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                mercado = res.json()[0].get('question', 'Polymarket')[:25] if res.status_code == 200 else "Scanner"
                
                novo_log = {
                    "data": datetime.now().strftime("%d/%m %H:%M"),
                    "mercado": mercado,
                    "lado": bot_config["preference"],
                    "resultado": "SINCRO_REAL 📡"
                }
                historico.insert(0, novo_log)
                historico = historico[:20]
                salvar_dados(historico)
            except: pass
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(loop_principal())

# --- INTERFACE COM SALDO REAL ---
@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    try:
        # Lendo POL Real
        pol_raw = w3.eth.get_balance(w3.to_checksum_address(WALLET_ADDRESS))
        pol_real = w3.from_wei(pol_raw, 'ether')
        
        # Lendo USDC Real
        usdc_raw = usdc_instancia.functions.balanceOf(w3.to_checksum_address(WALLET_ADDRESS)).call()
        usdc_real = usdc_raw / 10**6 # USDC tem 6 decimais
        
        saldos = {"pol": f"{pol_real:.2f}", "usdc": f"{usdc_real:.2f}"}
    except Exception as e:
        print(f"Erro saldo: {e}")
        saldos = {"pol": "0.00", "usdc": "0.00"}

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": WALLET_ADDRESS,
        "usdc": saldos["usdc"],
        "pol": saldos["pol"],
        "bot": bot_config,
        "historico": historico
    })

@app.post("/toggle_bot")
async def config(status: str = Form(...), preference: str = Form(...)):
    bot_config.update({"status": status, "preference": preference})
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def login(pin: str = Form(...)):
    return RedirectResponse(url="/dashboard", status_code=303) if pin == PIN_SISTEMA else "Erro"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))