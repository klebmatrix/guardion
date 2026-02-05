import os, asyncio, json, uvicorn, httpx
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES ---
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PRIV_KEY = os.getenv("private_key", "").strip()
if PRIV_KEY and not PRIV_KEY.startswith("0x"): PRIV_KEY = "0x" + PRIV_KEY

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
EXCHANGE_ADDR = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Alvos expandidos para maior volume
bot_config = {
    "status": "OFF", 
    "alvos": ["BITCOIN", "BTC", "ETH", "FED", "TRUMP", "ELON", "WAR", "STOCKS", "USA"],
    "min_price": 0.10, # Só entra se pagar pelo menos 25% de lucro
    "max_price": 0.75  # Evita entrar em aposta que já está quase decidida
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

async def executa_compra_inteligente(token_id, title, preco):
    try:
        tx_data = "0x4b665675" + token_id.replace('0x','').zfill(64)
        tx = {
            'nonce': w3.eth.get_transaction_count(WALLET),
            'to': w3.to_checksum_address(EXCHANGE_ADDR),
            'value': 0, 'gas': 500000,
            'gasPrice': int(w3.eth.gas_price * 1.5),
            'data': tx_data, 'chainId': 137
        }
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        w3.eth.send_raw_transaction(signed.raw_transaction)
        registrar_log(f"LUCRO ESTIM: {round((1-preco)*100)}%", "TIRO 🔥", "COMPRADO")
        return True
    except: return False

# --- MOTOR COM ANÁLISE DE MERCADO ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Busca os 20 mercados com mais volume no momento
                    res = await client.get("https://gamma-api.polymarket.com/events?active=true&limit=20&sort=volume:desc")
                    if res.status_code == 200:
                        encontrado_no_ciclo = False
                        for event in res.json():
                            title = str(event.get('title', '')).upper()
                            
                            # 1. Filtro de Palavra-Chave
                            if any(p in title for p in bot_config["alvos"]):
                                markets = event.get('markets', [])
                                if not markets: continue
                                
                                m_id = markets[0].get('id')
                                if m_id in comprados: continue

                                # 2. Filtro de Preço (Odds)
                                try:
                                    prices = markets[0].get('outcomePrices', [])
                                    if not prices: continue
                                    preco_yes = float(prices[0])
                                    
                                    if bot_config["min_price"] <= preco_yes <= bot_config["max_price"]:
                                        registrar_log(f"{title[:12]}.. @ {preco_yes}", "ANÁLISE", "FILÉ MIGNON")
                                        if await executa_compra_inteligente(m_id, title, preco_yes):
                                            comprados.add(m_id)
                                            encontrado_no_ciclo = True
                                            break # Dá um tiro por vez para não esgotar o saldo num só
                                    else:
                                        # Log silencioso de por que não comprou
                                        status_preco = "MUITO CARO" if preco_yes > bot_config["max_price"] else "MUITO RISCO"
                                        print(f"Pulando {title[:10]}: {status_preco} ({preco_yes})")
                                except: continue
                                
                        if not encontrado_no_ciclo:
                            registrar_log("Aguardando Oportunidade", "INTELIGENCIA", "BUSCA")
            except Exception as e:
                print(f"Erro no Motor: {e}")
        await asyncio.sleep(12) # Velocidade de sniper

@app.on_event("startup")
async def startup_event():
    if not os.path.exists("logs.json"):
        with open("logs.json", "w") as f: json.dump([], f)
    asyncio.create_task(sniper_loop())

# --- ROTAS (LOGIN / DASHBOARD / TOGGLE / DESTRAVAR) ---
@app.get("/", response_class=HTMLResponse)
async def login(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar(pin: str = Form(...)):
    if pin.strip() == str(os.getenv("guardiao", "20262026")).strip():
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("PIN INCORRETO.")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    pol, usdc = 0, 0
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
    registrar_log(f"Analista {status}", "SISTEMA", "MODO")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/destravar")
async def destravar_manual():
    try:
        abi = [{"constant":False,"inputs":[{"name":"_s","type":"address"},{"name":"_v","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"}]
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=abi)
        tx = c.functions.approve(w3.to_checksum_address(EXCHANGE_ADDR), 2**256-1).build_transaction({
            'from': WALLET, 'nonce': w3.eth.get_transaction_count(WALLET),
            'gas': 100000, 'gasPrice': int(w3.eth.gas_price * 1.5)
        })
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        w3.eth.send_raw_transaction(signed.raw_transaction)
        registrar_log("USDC DESTRAVADO", "BLOCKCHAIN", "SUCESSO ✅")
    except: registrar_log("Erro no Destrave", "ERRO", "FALHA")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))