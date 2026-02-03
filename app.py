import os
import asyncio
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES DE AMBIENTE ---
PIN_SISTEMA = os.getenv("guardiao", "123456")
PRIV_KEY = os.getenv("private_key")
WALLET_ADDRESS = "0x...E43E" # Sua carteira real
RPC_POLYGON = "https://polygon-rpc.com"

# Conexão Blockchain
w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

# --- ESTADO DO SISTEMA ---
bot_config = {"status": "OFF", "preference": "YES"}
historico = []
saldo_atual = {"usdc": "14.44", "pol": "1.25"}

# --- LÓGICA DE OPERAÇÃO REAL ---
async def monitorar_e_operar():
    """ Loop que roda 24/7 enquanto o servidor estiver 'acordado' """
    while True:
        if bot_config["status"] == "ON":
            agora = datetime.now().strftime("%H:%M:%S")
            print(f"[{agora}] 🤖 Guardião escaneando oportunidades...")
            
            # Aqui o bot faria a chamada de API e usaria a PRIV_KEY
            # para assinar a transação caso encontrasse o alvo.
            
            # Simulação de log de monitoramento
            if len(historico) > 20: historico.pop() # Limpa histórico antigo
        
        await asyncio.sleep(300) # Verifica a cada 5 minutos (sincronizado com UptimeRobot)

@app.on_event("startup")
async def startup_event():
    # Inicia o loop do robô em segundo plano
    asyncio.create_task(monitorar_e_operar())

# --- ROTAS DE INTERFACE ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar(pin: str = Form(...)):
    if pin == PIN_SISTEMA:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<h1>PIN INCORRETO</h1><a href='/'>Voltar</a>")

@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": WALLET_ADDRESS,
        "usdc": saldo_atual["usdc"],
        "pol": saldo_atual["pol"],
        "bot": bot_config,
        "historico": historico
    })

@app.post("/toggle_bot")
async def atualizar_config(status: str = Form(...), preference: str = Form(...)):
    bot_config["status"] = status
    bot_config["preference"] = preference
    
    # Registro de alteração no histórico
    log = {
        "data": datetime.now().strftime("%d/%m %H:%M"),
        "mercado": "CONFIGURAÇÃO",
        "lado": preference,
        "resultado": f"BOT {status}"
    }
    historico.insert(0, log)
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)