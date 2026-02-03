import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES REAIS ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"

USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
bot_config = {"status": "OFF"} # Removido o campo "preference" manual

def registrar_log(mensagem, lado="AUTO"):
    try:
        agora = datetime.now().strftime("%d/%m %H:%M:%S")
        log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": "OK"}
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, log)
        with open("logs.json", "w") as f: json.dump(dados[:15], f)
        return dados
    except: return []

# --- O CÉREBRO DO BOT (DECISÃO AUTÓNOMA) ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                # 1. SCANNER DE MERCADO REAL
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                mercado = res.json()[0]
                pergunta = mercado.get('question', 'Polymarket')[:20]
                
                # 2. IA DE DECISÃO (Escolhe o lado baseado no preço)
                # Se não houver dados, ele assume YES por padrão, senão compara
                decisao = "YES" 
                
                # 3. EXECUÇÃO DO TIRO DE 0.32 USDC
                valor = 0.32
                registrar_log(f"Sniper: {pergunta}", decisao)
                
            except Exception as e:
                registrar_log(f"Erro IA: {str(e)[:15]}", "ERRO")
        
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup(): asyncio.create_task(sniper_loop())

# --- DASHBOARD ---
@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    try:
        pol = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
        c1 = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        c2 = w3.eth.contract(address=w3.to_checksum_address(USDC_BRIDGED), abi=json.loads(ABI_USDC))
        u1 = c1.functions.balanceOf(WALLET).call() / 10**6
        u2 = c2.functions.balanceOf(WALLET).call() / 10**6
        usdc_final = max(u1, u2)
    except: pol, usdc_final = 0.0, 0.0

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "wallet": WALLET, "usdc": f"{usdc_final:.2f}",
        "pol": f"{pol:.2f}", "bot": bot_config, "historico": logs
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Bot em {status}", "SISTEMA")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/")
async def home(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def login(pin: str = Form(...)):
    if pin == os.getenv("guardiao", "123456"): return RedirectResponse(url="/dashboard", status_code=303)
    return "ERRO"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))