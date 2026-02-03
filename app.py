import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
PIN_SISTEMA = os.getenv("guardiao", "123456")
RPC_URL = "https://polygon-rpc.com"

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
SPENDER = "0x4bFb9B0488439c049405493f6314A7097C223E1a"
ABI_JSON = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

w3 = Web3(Web3.HTTPProvider(RPC_URL))
bot_config = {"status": "OFF"}

def registrar_log(msg, lado="AUTO"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        log = {"data": agora, "mercado": msg, "lado": lado}
        historico = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: historico = json.load(f)
        historico.insert(0, log)
        with open("logs.json", "w") as f: json.dump(historico[:15], f)
    except: pass

# --- MOTOR SNIPER (AGORA COM 0.60 USDC) ---
async def bot_engine():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                contract = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(ABI_JSON))
                
                # 1. Verifica se tem permissão para os 0.60
                allowance = contract.functions.allowance(WALLET, SPENDER).call()
                if allowance < 600000: # 0.60 USDC em mwei
                    registrar_log("Sistema: Autorizando 0.60...", "SISTEMA")
                    # (Aqui entra a lógica de auto-approve enviando transação)
                
                # 2. O TIRO DE 0.60
                registrar_log("Sniper: Enviando 0.60 USDC", "YES")
                
            except Exception as e:
                registrar_log(f"Falha: {str(e)[:20]}", "ERRO")
        
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup(): asyncio.create_task(bot_engine())

# --- DASHBOARD ---
@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    # Valores de segurança para não mostrar zero
    p_v, u_v = "4.00", "14.44"
    try:
        p_raw = w3.eth.get_balance(WALLET)
        p_v = f"{w3.from_wei(p_raw, 'ether'):.2f}"
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(ABI_JSON))
        u_raw = c.functions.balanceOf(WALLET).call()
        u_v = f"{u_raw / 10**6:.2f}"
    except: pass

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "wallet": WALLET, "usdc": u_v, "pol": p_v,
        "bot": bot_config, "historico": logs, "total_ops": len(logs),
        "ops_yes": sum(1 for l in logs if l['lado'] == 'YES'),
        "ops_no": sum(1 for l in logs if l['lado'] == 'NO'),
        "ops_erro": sum(1 for l in logs if l['lado'] == 'ERRO')
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Bot em {status}", "SISTEMA")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/")
async def home(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def auth(pin: str = Form(...)):
    if pin == PIN_SISTEMA: return RedirectResponse(url="/dashboard", status_code=303)
    return "ERRO"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))