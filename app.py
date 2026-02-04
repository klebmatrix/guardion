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

# Contratos (USDC Nativo e Polymarket Exchange)
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

# Configuração Web3
w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Estado do Bot
bot_config = {"status": "OFF", "preference": "YES"}
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","bool":"bool"}],"type":"function"}]'

# --- GESTÃO DE LOGS ---
def registrar_log(mensagem, lado="SCAN", resultado="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado}
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, log)
        with open("logs.json", "w") as f: json.dump(dados[:20], f)
        return dados
    except: return []

# --- MOTOR SNIPER (INTERVALO DE 5 MINUTOS) ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                registrar_log("Iniciando varredura (Ciclo 5m)", "SISTEMA", "LOOP")
                
                account = w3.eth.account.from_key(PRIV_KEY)
                contract = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
                
                # 1. Verifica Permissão de Gastos
                allowance = contract.functions.allowance(account.address, w3.to_checksum_address(CTF_EXCHANGE)).call()
                
                if allowance >= (1 * 10**6):
                    # 2. Busca Oportunidade na API da Polymarket
                    res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                    mercados = res.json()
                    alvo = mercados[0] # Exemplo: pega o mercado mais recente
                    
                    if "Bitcoin" in alvo.get('question', ''):
                        registrar_log(f"Alvo: {alvo['question'][:20]}", "TRADE", "EXECUTADO ✅")
                        # Trava de segurança para conferência
                        bot_config["status"] = "OFF"
                    else:
                        registrar_log("Monitorando mercados...", "IA", "SCAN")
                else:
                    registrar_log("Necessário Aprovar USDC no Dashboard", "AÇÃO", "BLOQUEADO")
            
            except Exception as e:
                registrar_log(f"Erro no Motor: {str(e)[:15]}", "ERRO", "FALHA")
        
        # AGUARDA 5 MINUTOS (300 segundos)
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sniper_loop())

# --- ROTAS WEB (INTERFACE) ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar_login(pin: str = Form(...)):
    # PIN definido nas variáveis de ambiente do Render (chave: guardiao)
    if pin == os.getenv("guardiao", "123456"):
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<h2>PIN INCORRETO</h2><a href='/'>Voltar</a>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        # Puxa saldos reais da rede
        bal_pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        bal_usdc = round(c.functions.balanceOf(WALLET).call() / 1e6, 2)
    except:
        bal_pol, bal_usdc = 0.0, 0.0

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": WALLET,
        "pol": bal_pol,
        "usdc": bal_usdc,
        "bot": bot_config,
        "historico": logs
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Bot alterado para {status}", "SISTEMA", "OK")
    return RedirectResponse(url="/dashboard", status_code=303)

# Comando para rodar: uvicorn app:app --host 0.0.0.0 --port $PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)