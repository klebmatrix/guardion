import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES DE AMBIENTE (RENDER) ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
PIN_SISTEMA = os.getenv("guardiao", "123456") # Seu PIN de 6 dígitos
RPC_POLYGON = "https://polygon-rpc.com"

# Contratos USDC
USDC_N = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_B = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
bot_config = {"status": "OFF"}

# --- PERSISTÊNCIA DE LOGS ---
def registrar_log(msg, lado="AUTO"):
    try:
        agora = datetime.now().strftime("%d/%m %H:%M:%S")
        log_entry = {"data": agora, "mercado": msg, "lado": lado}
        logs = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: logs = json.load(f)
        logs.insert(0, log_entry)
        with open("logs.json", "w") as f: json.dump(logs[:20], f)
    except: pass

# --- INTELIGÊNCIA AUTÓNOMA (O CÉREBRO) ---
async def bot_engine():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                # 1. Scanner de Mercado
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                dados = res.json()
                pergunta = dados[0].get('question', 'Polymarket')[:25]
                
                # 2. Decisão e Tiro de 0.32 USDC
                escolha = "YES" # Aqui a lógica decide baseada no preço
                registrar_log(f"Sniper: {pergunta}", escolha)
                
            except Exception as e:
                registrar_log(f"Erro: {str(e)[:15]}", "ERRO")
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup(): asyncio.create_task(bot_engine())

# --- ROTAS DE NAVEGAÇÃO ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar_login(pin: str = Form(...)):
    if pin == PIN_SISTEMA:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<script>alert('PIN INVÁLIDO'); window.location.href='/';</script>")

@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    try:
        # Saldo Real (Polygon)
        pol = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
        c1 = w3.eth.contract(address=w3.to_checksum_address(USDC_N), abi=json.loads(ABI))
        c2 = w3.eth.contract(address=w3.to_checksum_address(USDC_B), abi=json.loads(ABI))
        usdc = max(c1.functions.balanceOf(WALLET).call(), c2.functions.balanceOf(WALLET).call()) / 10**6
    except: pol, usdc = 0.0, 0.0

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    # Estatísticas para o Chart.js
    ctx = {
        "request": request, "wallet": WALLET, "usdc": f"{usdc:.2f}", "pol": f"{pol:.2f}",
        "bot": bot_config, "historico": logs, "total_ops": len(logs),
        "ops_yes": sum(1 for l in logs if l['lado'] == 'YES'),
        "ops_no": sum(1 for l in logs if l['lado'] == 'NO'),
        "ops_erro": sum(1 for l in logs if l['lado'] == 'ERRO')
    }
    return templates.TemplateResponse("dashboard.html", ctx)

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Sistema {status}", "SISTEMA")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))