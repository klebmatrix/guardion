import os, asyncio, json, requests, uvicorn
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
USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
CTF_EXCHANGE = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

bot_config = {"status": "OFF"}
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

# --- MOTOR SNIPER (5 MINUTOS) ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            agora = datetime.now().strftime("%H:%M:%S")
            print(f"[{agora}] Bot em varredura ativa...")
            # Lógica de trade aqui
        await asyncio.sleep(300) # 300 segundos = 5 minutos

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sniper_loop())

# --- ROTAS ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar_login(pin: str = Form(...)):
    # Puxa o PIN de 8 dígitos da variável 'guardiao' do Render
    # O .strip() remove espaços acidentais
    pin_real = str(os.getenv("guardiao", "12345678")).strip()
    
    if pin.strip() == pin_real:
        return RedirectResponse(url="/dashboard", status_code=303)
    
    return HTMLResponse(f"""
        <body style='background:#111;color:white;text-align:center;padding-top:50px;font-family:sans-serif;'>
            <h2 style='color:red'>❌ PIN INCORRETO</h2>
            <p>O PIN de 8 dígitos não confere com a variável 'guardiao'.</p>
            <p>Verifique as configurações no painel do Render.</p>
            <a href='/' style='color:cyan'>Voltar e tentar novamente</a>
        </body>
    """)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        pol = round(w3.from_wei(w3.eth.get_balance(WALLET), 'ether'), 4)
        c = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        usdc = round(c.functions.balanceOf(WALLET).call() / 1e6, 2)
    except: pol, usdc = 0, 0
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "wallet": WALLET, "pol": pol, "usdc": usdc, "bot": bot_config, "historico": []
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)