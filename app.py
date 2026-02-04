import os, asyncio, json, uvicorn, httpx
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGS ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
# Tratamento da chave: remove espaços e garante formato hexadecimal
RAW_KEY = os.getenv("private_key", "").strip()
if RAW_KEY and not RAW_KEY.startswith("0x"):
    RAW_KEY = "0x" + RAW_KEY

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
EXCHANGE_ADDR = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

bot_config = {"status": "OFF", "alvos": ["BITCOIN", "BTC", "ETH", "FED", "TRUMP"]}
comprados = set()

def registrar_log(msg, lado="SCAN", res="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, {"data": agora, "mercado": msg, "lado": lado, "resultado": res})
        with open("logs.json", "w") as f: json.dump(dados[:12], f)
    except: pass

# --- FUNÇÃO DE TIRO CORRIGIDA ---
async def executa_compra_bruta(token_id, title):
    try:
        if not RAW_KEY:
            registrar_log("Chave Ausente", "ERRO", "FALHA")
            return False

        nonce = w3.eth.get_transaction_count(WALLET)
        tx_data = "0x4b665675" + token_id.replace('0x','').zfill(64)
        
        tx = {
            'nonce': nonce,
            'to': w3.to_checksum_address(EXCHANGE_ADDR),
            'value': 0,
            'gas': 500000,
            'maxFeePerGas': w3.to_wei('200', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('50', 'gwei'),
            'data': tx_data,
            'chainId': 137
        }

        # Método de assinatura mais robusto
        signed_tx = w3.eth.account.sign_transaction(tx, RAW_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction) # Use raw_transaction (snake_case)
        
        registrar_log(f"TIRO DADO: {title[:10]}", "BLOCKCHAIN", "SUCESSO 🔥")
        return True
    except Exception as e:
        registrar_log(f"Erro: {str(e)[:15]}", "WEB3", "FALHA")
        print(f"ERRO DETALHADO: {e}")
        return False

# --- MOTOR SNIPER ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get("https://gamma-api.polymarket.com/events?active=true&limit=15&sort=volume:desc")
                    if res.status_code == 200:
                        mercados = res.json()
                        for m in mercados:
                            title = str(m.get('title', '')).upper()
                            m_id = m.get('id', '')
                            if any(p in title for p in bot_config["alvos"]) and m_id not in comprados:
                                if await executa_compra_bruta(m_id, title):
                                    comprados.add(m_id)
                                    break
                        else:
                            registrar_log("Buscando Alvos", "SCAN", "FAST")
            except Exception as e:
                pass
        await asyncio.sleep(20)

@app.on_event("startup")
async def startup_event():
    if not os.path.exists("logs.json"):
        with open("logs.json", "w") as f: json.dump([], f)
    asyncio.create_task(sniper_loop())

# --- ROTAS ---
@app.get("/", response_class=HTMLResponse)
async def login(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar(pin: str = Form(...)):
    if pin.strip() == str(os.getenv("guardiao", "20262026")).strip():
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("PIN INCORRETO.")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    pol, usdc = 0.0, 0.0
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        abi_u = '[{"constant":true,"inputs":[{"name":"_o","type":"address"}],"name":"balanceOf","outputs":[{"name":"b","type":"uint256"}],"type":"function"}]'
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(abi_u))
        usdc = round(c.functions.balanceOf(WALLET).call() / 1e6, 2)
    except: pass
    
    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)
    return templates.TemplateResponse("dashboard.html", {"request": request, "wallet": WALLET, "pol": pol, "usdc": usdc, "bot": bot_config, "historico": logs})

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Motor {status}", "SISTEMA", "MODO")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))