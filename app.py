import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# --- INICIALIZAÇÃO ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES DO MIX ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

# Conexão Web3
w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Estado Global e ABI
bot_config = {"status": "OFF"}
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

# --- GESTÃO DE LOGS ---
def registrar_log(mensagem, lado="SCAN", resultado="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado}
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, log)
        # Mantém apenas os últimos 15 registros para não pesar
        with open("logs.json", "w") as f: json.dump(dados[:15], f)
    except: pass

# --- MOTOR SNIPER (VARREDURA REAL A CADA 5 MINUTOS) ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                # 1. Busca mercados reais na API CLOB da Polymarket
                url = "https://clob.polymarket.com/markets"
                res = requests.get(url, timeout=15)
                
                if res.status_code == 200:
                    mercados = res.json()
                    # Filtra mercados relacionados a Bitcoin (ou mude para o que preferir)
                    alvos = [m for m in mercados if "Bitcoin" in m.get('question', '')]
                    
                    if alvos:
                        pergunta = alvos[0].get('question', 'Mercado Ativo')
                        registrar_log(f"Alvo Detectado: {pergunta[:30]}...", "AUTO", "LISTADO")
                        print(f"🎯 Sniper ativo em: {pergunta}")
                    else:
                        registrar_log("Nenhum alvo Bitcoin encontrado", "SCAN", "BUSCANDO")
                else:
                    registrar_log("Falha na API Polymarket", "API", "ERRO")
            
            except Exception as e:
                registrar_log(f"Erro no Motor: {str(e)[:15]}", "ERRO", "FALHA")
        
        # Intervalo de 5 minutos (300 segundos)
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sniper_loop())

# --- ROTAS DA INTERFACE ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar_login(pin: str = Form(...)):
    pin_real = str(os.getenv("guardiao")).strip()
    if pin.strip() == pin_real:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<h2 style='color:red;text-align:center;margin-top:50px;'>PIN INCORRETO</h2><p style='text-align:center;'><a href='/'>Voltar</a></p>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        # Saldo POL (Gás)
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        # Saldo USDC (Banca)
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        usdc = round(c.functions.balanceOf(WALLET).call() / 1e6, 2)
    except:
        pol, usdc = 0, 0

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": WALLET,
        "pol": pol,
        "usdc": usdc,
        "bot": bot_config,
        "historico": logs
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Bot em modo {status}", "SISTEMA", "OK")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)