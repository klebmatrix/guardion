import os, asyncio, json, uvicorn, httpx
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES DE FERRO ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
EXCHANGE_ADDR = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

# Sistema de Conexão com Backup
RPCS = ["https://polygon-rpc.com", "https://1rpc.io/matic", "https://rpc.ankr.com/polygon"]
def get_w3():
    for rpc in RPCS:
        w = Web3(Web3.HTTPProvider(rpc))
        if w.is_connected():
            w.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            return w
    return None

w3 = get_w3()
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

# --- DESTRAVE (APPROVE) ---
async def liberar_usdc_agora():
    try:
        registrar_log("Destravando USDC...", "WEB3", "WAIT")
        # ABI Direta para não dar erro de parse
        abi = [{"constant":False,"inputs":[{"name":"_s","type":"address"},{"name":"_v","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"}]
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=abi)
        
        tx = c.functions.approve(w3.to_checksum_address(EXCHANGE_ADDR), 2**256-1).build_transaction({
            'from': WALLET,
            'nonce': w3.eth.get_transaction_count(WALLET),
            'gas': 120000,
            'gasPrice': int(w3.eth.gas_price * 1.5)
        })
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        registrar_log(f"TX: {tx_hash.hex()[:6]}", "BLOCKCHAIN", "LIBERADO ✅")
        await asyncio.sleep(15)
        return True
    except: return False

# --- COMPRA (BUY) ---
async def executa_compra_bruta(token_id, title):
    try:
        # Comando de compra real para a Polymarket
        tx_data = "0x4b665675" + token_id.replace('0x','').zfill(64)
        tx = {
            'nonce': w3.eth.get_transaction_count(WALLET),
            'to': w3.to_checksum_address(EXCHANGE_ADDR),
            'value': 0, 'gas': 500000,
            'gasPrice': int(w3.eth.gas_price * 1.3),
            'data': tx_data, 'chainId': 137
        }
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        w3.eth.send_raw_transaction(signed.rawTransaction)
        registrar_log(f"COMPRA: {title[:10]}", "BLOCKCHAIN", "DINHEIRO SAIU 🔥")
        return True
    except: return False

# --- MOTOR ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON":
            try:
                if not os.path.exists("liberado.txt"):
                    if await liberar_usdc_agora():
                        with open("liberado.txt", "w") as f: f.write("ok")
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get("https://gamma-api.polymarket.com/events?active=true&limit=10&sort=volume:desc")
                    if res.status_code == 200:
                        for m in res.json():
                            title = str(m.get('title', '')).upper()
                            m_id = m.get('id')
                            if any(p in title for p in bot_config["alvos"]) and m_id not in comprados:
                                if await executa_compra_bruta(m_id, title):
                                    comprados.add(m_id)
                                    break
                        else: registrar_log("Monitorando...", "SCAN", "FAST")
            except: pass
        await asyncio.sleep(20)

@app.on_event("startup")
async def startup_event():
    if not os.path.exists("logs.json"):
        with open("logs.json", "w") as f: json.dump([], f)
    asyncio.create_task(sniper_loop())

# --- INTERFACE ---
@app.get("/", response_class=HTMLResponse)
async def login(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar(pin: str = Form(...)):
    if pin.strip() == str(os.getenv("guardiao", "20262026")).strip():
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("PIN INCORRETO.")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    global w3
    if not w3 or not w3.is_connected(): w3 = get_w3()
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        abi_u = '[{"constant":true,"inputs":[{"name":"_o","type":"address"}],"name":"balanceOf","outputs":[{"name":"b","type":"uint256"}],"type":"function"}]'
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(abi_u))
        usdc = round(c.functions.balanceOf(WALLET).call() / 1e6, 2)
    except: pol, usdc = 0, 0
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