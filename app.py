import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- IDENTIDADE DO BOT ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
RPC_POLYGON = "https://polygon-rpc.com"
# Contrato do USDC Nativo e do USDC.e (tentaremos ambos)
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359" 
USDC_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
bot_config = {"status": "OFF", "preference": "YES"}

# --- HISTÓRICO AUTOMÁTICO (PERSISTENTE) ---
def registrar_evento(mensagem):
    try:
        agora = datetime.now().strftime("%d/%m %H:%M:%S")
        log = {"data": agora, "mercado": mensagem, "lado": bot_config["preference"], "resultado": "OK"}
        
        # Carrega, adiciona e salva
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, log)
        with open("logs.json", "w") as f: json.dump(dados[:15], f)
        return dados
    except: return []

# --- DASHBOARD REAL ---
@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    # 1. Lê POL
    pol_raw = w3.eth.get_balance(WALLET)
    pol = w3.from_wei(pol_raw, 'ether')
    
    # 2. Lê USDC (Tenta o contrato nativo)
    usdc_inst = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(USDC_ABI))
    usdc_raw = usdc_inst.functions.balanceOf(WALLET).call()
    usdc = usdc_raw / 10**6

    # 3. Atualiza histórico de "visita"
    historico_atual = registrar_evento("Check de Saldo")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": WALLET,
        "usdc": f"{usdc:.2f}",
        "pol": f"{pol:.2f}",
        "bot": bot_config,
        "historico": historico_atual
    })

# --- REGRAS DE ACESSO ---
@app.post("/entrar")
async def login(pin: str = Form(...)):
    if pin == os.getenv("guardiao", "123456"):
        return RedirectResponse(url="/dashboard", status_code=303)
    return "PIN ERRADO"

@app.get("/")
async def home(request: Request): return templates.TemplateResponse("login.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))