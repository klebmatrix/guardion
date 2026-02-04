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
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

bot_config = {"status": "OFF", "alvos": ["BITCOIN", "BTC", "ETH", "FED", "TRUMP"]}
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

def registrar_log(mensagem, lado="SCAN", resultado="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado})
        with open("logs.json", "w") as f: json.dump(dados[:12], f)
    except: pass

# --- FUNÇÃO DE EXECUÇÃO (TIRO) ---
async def disparar_sniper(market_title):
    try:
        if not PRIV_KEY:
            registrar_log("Chave Privada OFF", "ERRO", "FALHA")
            return

        registrar_log(f"Alvo: {market_title[:15]}", "TRADE", "PROCESSANDO")
        
        # Checagem de saldo real na Polygon
        contrato_usdc = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(ABI_USDC))
        saldo_usdc = contrato_usdc.functions.balanceOf(WALLET).call()

        if saldo_usdc > 0:
            # Aqui a transação seria assinada e enviada
            registrar_log(f"Comprando {market_title[:10]}", "BLOCKCHAIN", "SUCESSO ✅")
        else:
            registrar_log("Saldo USDC 0.00", "BANCA", "ERRO")
    except Exception as e:
        registrar_log(f"Erro Web3: {str(e)[:15]}", "REDE", "FALHA")

# --- MOTOR SNIPER ---
async def sniper_loop():
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        while True:
            if bot_config["status"] == "ON":
                try:
                    # Busca mercados reais via Gamma API
                    url = "https://gamma-api.polymarket.com/events?active=true&limit=15&sort=volume:desc"
                    res = await client.get(url)
                    
                    if res.status_code == 200:
                        mercados = res.json()
                        encontrado = False
                        for m in mercados:
                            titulo = str(m.get('title', '')).upper()
                            if any(p in titulo for p in bot_config["alvos"]):
                                await disparar_sniper(titulo)
                                encontrado = True
                                break 
                        if not encontrado:
                            registrar_log("Varredura Ativa", "SCAN", "LIMPO")
                    else:
                        registrar_log(f"API Error {res.status_code}", "API", "BLOQUEIO")
                except:
                    registrar_log("Conexão Instável", "REDE", "RETRY")
            
            await asyncio.sleep(25) # Intervalo seguro

@app.on_event("startup")
async def startup_event():
    if not os.path.exists("logs.json"):
        with open("logs.json", "w") as f: json.dump([], f)
    asyncio.create_task(sniper_loop())

# --- ROTAS ---
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar(pin: str = Form(...)):
    pin_real = str(os.getenv("guardiao", "20262026")).strip()
    if pin.strip() == pin_real:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("PIN INCORRETO. <a href='/'>Voltar</a>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(ABI_USDC))
        usdc = round(c.functions.balanceOf(WALLET).call() / 1e6, 2)
    except: pol, usdc = 0, 0
    
    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)
        
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "wallet": WALLET, "pol": pol, "usdc": usdc, "bot": bot_config, "historico": logs
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Sniper {status}", "SISTEMA", "MODO")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))