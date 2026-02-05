import os, asyncio, json, uvicorn, httpx
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONEXÃO E IDENTIDADE ---
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PRIV_KEY = os.getenv("private_key", "").strip()
if PRIV_KEY and not PRIV_KEY.startswith("0x"): PRIV_KEY = "0x" + PRIV_KEY

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
EXCHANGE_ADDR = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# --- ESTRATÉGIA AGRESSIVA ---
bot_config = {
    "status": "OFF", 
    "min_price": 0.15, # Lucro mínimo de 15%
    "max_price": 0.85, # Não entra em aposta ganha
    "min_volume": 5000 # Só entra se tiver pelo menos $5k rodando (evita mercados mortos)
}
comprados = set()

def registrar_log(msg, lado="SCAN", res="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, {"data": agora, "mercado": msg, "lado": lado, "resultado": res})
        with open("logs.json", "w") as f: json.dump(dados[:15], f)
    except: pass

async def executa_compra(token_id, title, preco):
    try:
        tx_data = "0x4b665675" + token_id.replace('0x','').zfill(64)
        tx = {
            'nonce': w3.eth.get_transaction_count(WALLET),
            'to': w3.to_checksum_address(EXCHANGE_ADDR),
            'value': 0, 'gas': 500000,
            'gasPrice': int(w3.eth.gas_price * 1.6),
            'data': tx_data, 'chainId': 137
        }
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        w3.eth.send_raw_transaction(signed.raw_transaction)
        registrar_log(f"TIRO: {title[:15]}", "OPERAÇÃO", "SUCESSO 🔥")
        return True
    except: return False

# --- MOTOR SNIPER DE ALTA FREQUÊNCIA ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Puxa os 50 mercados mais quentes do momento
                    res = await client.get("https://gamma-api.polymarket.com/events?active=true&limit=50&sort=volume:desc")
                    if res.status_code == 200:
                        eventos = res.json()
                        analisados = 0
                        
                        for ev in eventos:
                            analisados += 1
                            markets = ev.get('markets', [])
                            if not markets: continue
                            
                            m_id = markets[0].get('id')
                            if m_id in comprados: continue

                            # Filtro de Volume Real
                            vol = float(ev.get('volume', 0))
                            if vol < bot_config["min_volume"]: continue

                            # Filtro de Preço
                            try:
                                prices = markets[0].get('outcomePrices', [])
                                if not prices: continue
                                p_yes = float(prices[0])

                                if bot_config["min_price"] <= p_yes <= bot_config["max_price"]:
                                    title = ev.get('title', 'Mercado')
                                    if await executa_compra(m_id, title, p_yes):
                                        comprados.add(m_id)
                                        break # Um tiro por ciclo para segurança
                            except: continue
                        
                        registrar_log(f"Vigiando {analisados} mercados ativos", "RADAR", "ON")
            except: pass
        await asyncio.sleep(10) # 10 segundos para não ser banido pela API

@app.on_event("startup")
async def startup_event():
    if not os.path.exists("logs.json"):
        with open("logs.json", "w") as f: json.dump([], f)
    asyncio.create_task(sniper_loop())

# --- ROTAS INTERFACE ---
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
    registrar_log(f"Radar {status}", "SISTEMA", "MODO")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/destravar")
async def destravar():
    try:
        abi = [{"constant":False,"inputs":[{"name":"_s","type":"address"},{"name":"_v","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"}]
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=abi)
        tx = c.functions.approve(w3.to_checksum_address(EXCHANGE_ADDR), 2**256-1).build_transaction({
            'from': WALLET, 'nonce': w3.eth.get_transaction_count(WALLET),
            'gas': 100000, 'gasPrice': int(w3.eth.gas_price * 1.5)
        })
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        w3.eth.send_raw_transaction(signed.raw_transaction)
        registrar_log("USDC LIBERADO", "BLOCKCHAIN", "OK ✅")
    except: registrar_log("Erro Approve", "ERRO", "FALHA")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))