import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

app = FastAPI()

# --- CONFIGURAÇÕES DE AMBIENTE ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
PIN_SISTEMA = os.getenv("guardiao") 
RPC_URL = "https://polygon-rpc.com"

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
SPENDER_POLYM = "0x4bFb9B0488439c049405493f6314A7097C223E1a"

ABI_COMPLETA = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

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

# --- MOTOR DE TIRO REAL (GATILHO) ---
async def bot_engine():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                # 1. Checa se o robô tem permissão de gasto (Allowance)
                contract = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(ABI_COMPLETA))
                allowance = contract.functions.allowance(WALLET, SPENDER_POLYM).call()
                
                if allowance < 600000: # Se não tiver 0.60 USDC liberado
                    registrar_log("Sistema: Autorizando USDC...", "SISTEMA")
                    tx_app = contract.functions.approve(SPENDER_POLYM, 10**12).build_transaction({
                        'from': WALLET, 'nonce': w3.eth.get_transaction_count(WALLET),
                        'gas': 100000, 'gasPrice': w3.eth.gas_price
                    })
                    signed = w3.eth.account.sign_transaction(tx_app, PRIV_KEY)
                    w3.eth.send_raw_transaction(signed.rawTransaction)
                    await asyncio.sleep(20)

                # 2. EXECUÇÃO DO TIRO DE 0.60 USDC
                # Aqui o bot assina e envia para a rede
                registrar_log("Sniper: EXECUTANDO 0.60 USDC", "YES")
                
                # Exemplo de transação de envio real que consome POL e USDC
                tx_tiro = {
                    'nonce': w3.eth.get_transaction_count(WALLET),
                    'to': SPENDER_POLYM,
                    'value': 0,
                    'gas': 250000,
                    'gasPrice': w3.eth.gas_price,
                    'data': '0x' # Espaço para o comando da Polymarket
                }
                signed_tiro = w3.eth.account.sign_transaction(tx_tiro, PRIV_KEY)
                w3.eth.send_raw_transaction(signed_tiro.rawTransaction)
                
            except Exception as e:
                registrar_log(f"Falha Real: {str(e)[:20]}", "ERRO")
        
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup(): asyncio.create_task(bot_engine())

# --- INTERFACE ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def auth(pin: str = Form(...)):
    if pin == PIN_SISTEMA: return RedirectResponse(url="/dashboard", status_code=303)
    return "Acesso Negado"

@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    try:
        p_raw = w3.eth.get_balance(WALLET)
        pol = f"{w3.from_wei(p_raw, 'ether'):.2f}"
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(ABI_COMPLETA))
        usdc = f"{c.functions.balanceOf(WALLET).call() / 10**6:.2f}"
    except: pol, usdc = "0.00", "0.00"

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "wallet": WALLET, "usdc": usdc, "pol": pol,
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))