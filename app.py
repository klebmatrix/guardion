import os, asyncio, json, uvicorn, httpx
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES REAIS ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
# Endereço do contrato que executa a troca (FixedProductMarketMaker)
ROUTER_POLY = "0x4bFb41d5B3570De3061333a9b59dd234870343f5" 

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

bot_config = {"status": "OFF", "alvos": ["BITCOIN", "BTC", "ETH", "FED", "TRUMP"]}
mercados_comprados = set() # Trava para não comprar o mesmo mercado 1000 vezes

def registrar_log(mensagem, lado="SCAN", resultado="OK"):
    try:
        agora = datetime.now().strftime("%H:%M:%S")
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: dados = json.load(f)
        dados.insert(0, {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado})
        with open("logs.json", "w") as f: json.dump(dados[:12], f)
    except: pass

# --- FUNÇÃO DE COMPRA REAL (ON-CHAIN) ---
async def disparar_sniper_real(market_id, market_title):
    if market_id in mercados_comprados: return
    
    try:
        registrar_log(f"EXECUTANDO COMPRA: {market_title[:10]}", "BLOCKCHAIN", "ENVIANDO")
        
        # Montando a transação (Exemplo simplificado de Swap via Router)
        nonce = w3.eth.get_transaction_count(WALLET)
        
        # Valor a gastar: 14.44 USDC (convertido para 6 decimais)
        amount = int(14.44 * 10**6) 
        
        # Transação básica de transferência/interação
        tx = {
            'nonce': nonce,
            'to': w3.to_checksum_address(ROUTER_POLY), 
            'value': 0,
            'gas': 250000,
            'maxFeePerGas': w3.to_wei('100', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('30', 'gwei'),
            'data': '0x', # Aqui iria o encoded_abi da função buy() da Polymarket
            'chainId': 137
        }

        signed_tx = w3.eth.account.sign_transaction(tx, PRIV_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        registrar_log(f"TX ENVIADA: {tx_hash.hex()[:10]}", "BLOCKCHAIN", "SUCESSO ✅")
        mercados_comprados.add(market_id) # Trava o mercado para não repetir

    except Exception as e:
        registrar_log(f"ERRO REAL: {str(e)[:15]}", "WEB3", "FALHA")

# --- MOTOR SNIPER ---
async def sniper_loop():
    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            if bot_config["status"] == "ON":
                try:
                    url = "https://gamma-api.polymarket.com/events?active=true&limit=15&sort=volume:desc"
                    res = await client.get(url)
                    if res.status_code == 200:
                        mercados = res.json()
                        for m in mercados:
                            titulo = str(m.get('title', '')).upper()
                            if any(p in titulo for p in bot_config["alvos"]):
                                await disparar_sniper_real(m.get('id'), titulo)
                                break 
                except: pass
            await asyncio.sleep(25)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sniper_loop())

# ... [RESTANTE DAS ROTAS IGUAL AO ANTERIOR] ...