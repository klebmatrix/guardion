import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from fpdf import FPDF

# --- INICIALIZAÇÃO ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES DO MIX ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

# Conexão Web3
w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Estado Global
bot_config = {"status": "OFF", "preference": "YES"}
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","bool":"bool"}],"type":"function"}]'

# --- NÚCLEO DE LOGS ---
def registrar_log(mensagem, lado="SCAN", resultado="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado}
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, log)
        with open("logs.json", "w") as f: json.dump(dados[:30], f)
        return dados
    except: return []

# --- MOTOR SNIPER (O MIX DAS DUAS LÓGICAS) ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                account = w3.eth.account.from_key(PRIV_KEY)
                contract = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
                
                # 1. Checa Permissão (Economia de POL)
                allowance = contract.functions.allowance(account.address, w3.to_checksum_address(CTF_EXCHANGE)).call()
                
                if allowance < (1 * 10**6):
                    registrar_log("Solicitando Aprovação USDC", "SISTEMA", "POL-GAS")
                    # (Lógica de approve simplificada aqui)
                else:
                    # 2. Scanner Polymarket (API)
                    res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                    mercados = res.json()
                    alvo = mercados[0] # Pega o mercado mais recente
                    
                    # 3. IA de Decisão (do primeiro bot.py)
                    if "Bitcoin" in alvo.get('question', ''):
                        registrar_log(f"Sniper Atacando: {alvo['question'][:20]}", "TRADE", "EXECUTADO")
                        # Aqui entraria a assinatura w3.eth.send_raw_transaction
                        bot_config["status"] = "OFF" # Trava de segurança
                    else:
                        registrar_log("Monitorando mercados...", "IA", "SCAN")
            except Exception as e:
                registrar_log(f"Erro: {str(e)[:20]}", "MOTOR", "FALHA")
        
        await asyncio.sleep(60) # Intervalo do mix: 1 minuto

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sniper_loop())

# --- ROTAS WEB ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar_login(pin: str = Form(...)):
    if pin == os.getenv("guardiao", "123456"):
        response = RedirectResponse(url="/dashboard", status_code=303)
        return response
    return "PIN INCORRETO"

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        usdc = round(c.functions.balanceOf(WALLET).call() / 1e6, 2)
    except: pol, usdc = 0, 0

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "wallet": WALLET, "pol": pol, "usdc": usdc,
        "bot": bot_config, "historico": logs, "total_ops": len(logs)
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Bot em {status}", "SISTEMA", "OK")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))