import os, asyncio, json, uvicorn, httpx
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGS ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

bot_config = {"status": "OFF"}
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

def registrar_log(mensagem, lado="SCAN", resultado="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado}
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, log)
        with open("logs.json", "w") as f: json.dump(dados[:12], f)
    except: pass

# --- MOTOR ASSÍNCRONO COM HTTPX ---
async def sniper_loop():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:
        while True:
            if bot_config["status"] == "ON":
                try:
                    # Usando o Gamma API (mais estável para varredura rápida)
                    url = "https://gamma-api.polymarket.com/events?active=true&limit=10"
                    res = await client.get(url)
                    
                    if res.status_code == 200:
                        mercados = res.json()
                        # Filtro inteligente
                        alvos = [m for m in mercados if any(x in str(m.get('title','')).upper() for x in ["BITCOIN", "BTC", "CRYPTO", "FED"])]
                        
                        if alvos:
                            nome = alvos[0]['title'][:25]
                            registrar_log(f"Alvo: {nome}", "AUTO", "LOCALIZADO 🎯")
                        else:
                            registrar_log("Varredura Ativa (Sem Alvos)", "SCAN", "LIMPO")
                    elif res.status_code == 429:
                        registrar_log("Rate Limit (Aguardando)", "AVISO", "SLOW")
                        await asyncio.sleep(60) # Pausa de 1 min se for limitado
                    else:
                        registrar_log(f"Erro HTTP {res.status_code}", "API", "FALHA")
                except Exception as e:
                    registrar_log("Falha de Rota", "REDE", "RETRY")
            
            # 30 segundos é o ideal para o Render não derrubar sua conexão
            await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sniper_loop())

# --- ROTAS ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar_login(pin: str = Form(...)):
    pin_real = str(os.getenv("guardiao", "20262026")).strip()
    if pin.strip() == pin_real:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("PIN INCORRETO.")

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
    return templates.TemplateResponse("dashboard.html", {"request": request, "wallet": WALLET, "pol": pol, "usdc": usdc, "bot": bot_config, "historico": logs})

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Bot em {status}", "SISTEMA", "MODO")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))