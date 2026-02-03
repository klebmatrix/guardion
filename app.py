import os, asyncio, json, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3

base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

app = FastAPI()

# --- CONFIGURAÇÕES ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
private_key = os.getenv("private_key", "").strip() 
guardiao = os.getenv("guardiao") 

# Usando um RPC alternativo para evitar delay de atualização
w3 = Web3(Web3.HTTPProvider("https://polygon.llamarpc.com"))
bot_config = {"status": "OFF"}

USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
SPENDER_POLYM = "0x4bFb9B0488439c049405493f6314A7097C223E1a"

def registrar_log(msg, lado="AUTO"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        log = {"data": agora, "mercado": msg, "lado": lado}
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, log)
        with open("logs.json", "w") as f: json.dump(dados[:15], f)
    except: pass

async def bot_engine():
    while True:
        if bot_config["status"] == "ON" and private_key:
            try:
                key = private_key if private_key.startswith('0x') else '0x' + private_key
                tx = {
                    'nonce': w3.eth.get_transaction_count(WALLET),
                    'to': w3.to_checksum_address(SPENDER_POLYM),
                    'value': 0,
                    'gas': 250000,
                    'gasPrice': w3.eth.gas_price,
                    'chainId': 137
                }
                signed = w3.eth.account.sign_transaction(tx, key)
                raw = getattr(signed, 'raw_transaction', getattr(signed, 'rawTransaction', None))
                if raw:
                    tx_hash = w3.eth.send_raw_transaction(raw)
                    registrar_log(f"TIRO REAL: {tx_hash.hex()[:10]}", "YES")
            except Exception as e:
                registrar_log(f"ERRO: {str(e)[:15]}", "ERRO")
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup(): asyncio.create_task(bot_engine())

# --- ROTA DO DASHBOARD COM CONSULTA REAL ---
@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    # Força a busca do saldo POL e USDC na blockchain AGORA
    try:
        pol_raw = w3.eth.get_balance(WALLET)
        pol_real = f"{w3.from_wei(pol_raw, 'ether'):.2f}"
        
        abi_minima = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
        contrato = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(abi_minima))
        usdc_real = f"{contrato.functions.balanceOf(WALLET).call() / 10**6:.2f}"
    except:
        pol_real, usdc_real = "Erro", "Erro"

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: logs = json.load(f)

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "wallet": WALLET, 
        "usdc": usdc_real, "pol": pol_real, # Aqui entram os valores reais capturados acima
        "bot": bot_config, "historico": logs, "total_ops": len(logs),
        "ops_yes": sum(1 for l in logs if l['lado'] == 'YES'),
        "ops_no": sum(1 for l in logs if l['lado'] == 'NO'),
        "ops_erro": sum(1 for l in logs if l['lado'] == 'ERRO')
    })

@app.get("/")
async def home(request: Request): return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def auth(pin: str = Form(...)):
    if pin == guardiao: return RedirectResponse(url="/dashboard", status_code=303)
    return "Negado"

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    bot_config["status"] = status
    registrar_log(f"Bot {status}", "SISTEMA")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))