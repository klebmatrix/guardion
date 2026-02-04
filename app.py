import os, asyncio, json, uvicorn, httpx
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGS TÉCNICAS REAIS ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
EXCHANGE_ADDR = "0x4bFb41d5B3570De3061333a9b59dd234870343f5"

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

bot_config = {"status": "OFF", "alvos": ["BITCOIN", "BTC", "ETH", "FED", "TRUMP"]}
comprados = set()

def registrar_log(msg, lado="SCAN", res="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, {"data": agora, "mercado": msg, "lado": lado, "resultado": res})
        with open("logs.json", "w") as f: json.dump(dados[:12], f)
    except: pass

# --- FUNÇÃO SECRETA: O DESTRAVE (APPROVE) ---
async def liberar_usdc_agora():
    try:
        registrar_log("Destravando USDC...", "SISTEMA", "WAIT")
        abi_app = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"}]'
        contrato = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=json.loads(abi_app))
        
        # Valor infinito para nunca mais travar
        tx = contrato.functions.approve(
            w3.to_checksum_address(EXCHANGE_ADDR), 
            115792089237316195423570985008687907853269984665640564039457584007913129639935
        ).build_transaction({
            'from': WALLET,
            'nonce': w3.eth.get_transaction_count(WALLET),
            'gas': 100000,
            'maxFeePerGas': w3.to_wei('150', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('40', 'gwei')
        })
        
        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        registrar_log(f"LIBERADO: {tx_hash.hex()[:6]}", "BLOCKCHAIN", "PRONTO ✅")
        await asyncio.sleep(10) # Espera a rede registrar
    except Exception as e:
        registrar_log("Erro no Destrave", "WEB3", "FALHA")

# --- FUNÇÃO DE TIRO REAL ---
async def executa_compra_bruta(token_id, market_title):
    try:
        # 14.44 USDC em 6 decimais
        tx_data = "0x4b665675" + token_id.replace('0x','').zfill(64) 
        
        tx = {
            'nonce': w3.eth.get_transaction_count(WALLET),
            'to': w3.to_checksum_address(EXCHANGE_ADDR),
            'value': 0,
            'gas': 450000,
            'maxFeePerGas': w3.to_wei('250', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('60', 'gwei'),
            'data': tx_data, 
            'chainId': 137
        }

        signed = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        registrar_log(f"COMPRA REAL: {market_title[:10]}", "BLOCKCHAIN", "SALDO SAIU 🔥")
        return True
    except Exception as e:
        registrar_log("Falha no Tiro", "WEB3", "ERRO")
        return False

# --- MOTOR SNIPER ---
async def sniper_loop():
    while True:
        if bot_config["status"] == "ON":
            try:
                # Primeiro, garante que o USDC está liberado uma única vez
                if not os.path.exists("liberado.txt"):
                    await liberar_usdc_agora()
                    with open("liberado.txt", "w") as f: f.write("ok")

                async with httpx.AsyncClient(timeout=10.0) as client:
                    url = "https://gamma-api.polymarket.com/events?active=true&limit=10&sort=volume:desc"
                    res = await client.get(url)
                    if res.status_code == 200:
                        for m in res.json():
                            title = str(m.get('title', '')).upper()
                            m_id = m.get('id')
                            if any(p in title for p in bot_config["alvos"]) and m_id not in comprados:
                                if await executa_compra_bruta(m_id, title):
                                    comprados.add(m_id)
                                    break
            except: pass
        await asyncio.sleep(20)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sniper_loop())

# [MANTENHA O RESTANTE DAS ROTAS DE LOGIN E DASHBOARD]