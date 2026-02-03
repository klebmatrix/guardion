import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONEXÃO E IDENTIDADE ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"

# Contratos (USDC e Polymarket Spender)
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
SPENDER = "0x4bFb9B0488439c049405493f6314A7097C223E1a"

# ABI ESSENCIAL PARA DESTRAVA
ABI_JSON = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
bot_config = {"status": "OFF"}

def registrar_log(msg, lado="AUTO"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        log = {"data": agora, "mercado": msg, "lado": lado}
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, log)
        with open("logs.json", "w") as f: json.dump(dados[:15], f)
    except: pass

# --- MOTOR DE EXECUÇÃO ---
async def bot_engine():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                contract = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(ABI_JSON))
                
                # 1. Checa Permissão (Allowance)
                allowance = contract.functions.allowance(WALLET, SPENDER).call()
                
                if allowance < 1000000: # Se menor que 1 USDC autorizado
                    registrar_log("Sistema: Enviando Destrava...", "SISTEMA")
                    
                    tx = contract.functions.approve(SPENDER, 10**12).build_transaction({
                        'from': WALLET,
                        'nonce': w3.eth.get_transaction_count(WALLET),
                        'gas': 100000,
                        'gasPrice': w3.eth.gas_price
                    })
                    
                    signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
                    w3.eth.send_raw_transaction(signed.rawTransaction)
                    registrar_log("Sistema: USDC DESTRAVADO!", "SISTEMA")
                    await asyncio.sleep(20) # Aguarda confirmação na rede

                # 2. IA de Tiro (Simulação de Ordem)
                registrar_log("Sniper: Ordem 0.32 USDC", "YES")
                
            except Exception as e:
                registrar_log(f"Erro: {str(e)[:20]}", "ERRO")
        
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup(): asyncio.create_task(bot_engine())

# --- ROTAS DASHBOARD ---
@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    try:
        pol = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(ABI_JSON))
        usdc = c.functions.balanceOf(WALLET).call() / 10**6
    except: pol, usdc = 0.0, 0.0

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "wallet": WALLET, "usdc": f"{usdc:.2f}", "pol": f"{pol:.2f}",
        "bot": bot_config, "historico": logs, "total_ops": len(logs),
        "ops_yes": sum(1 for l in logs if l['lado'] == 'YES'),
        "ops_no": sum(1 for l in logs if l['lado'] == 'NO'),
        "ops_erro": sum(1 for l in logs if l['lado'] == 'ERRO')
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Bot {status}", "SISTEMA")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/")
async def login(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def auth(pin: str = Form(...)):
    if pin == os.getenv("guardiao", "123456"): return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("ERRO")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))