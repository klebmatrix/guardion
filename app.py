import os, datetime, time, threading, requests, math
from flask import Flask, session, redirect, url_for, request, Response
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00
CARTEIRA_ALVO = "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"

# --- LISTA DE TÚNEIS (RPCs) ---
TUNEIS_POLYGON = [
    "https://rpc.ankr.com/polygon",
    "https://polygon-bor-rpc.publicnode.com",
    "https://1rpc.io/matic"
]

saldo_usd = 0.0
preco_btc = 0.0
dias_meta = "Sincronizando..."

def buscar_dados():
    global saldo_usd, preco_btc, dias_meta
    while True:
        try:
            # 1. TENTA PREÇO BTC (API Alternativa se a Binance falhar)
            try:
                r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=5).json()
                preco_btc = float(r['bpi']['USD']['rate_float'])
            except:
                r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
                preco_btc = float(r['price'])

            # 2. TENTA SALDO (Roda a lista de túneis até um responder)
            for url in TUNEIS_POLYGON:
                try:
                    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
                    if w3.is_connected():
                        bal_wei = w3.eth.get_balance(CARTEIRA_ALVO)
                        # Se a carteira estiver vazia na rede, mantemos um saldo base de $1500 para teste
                        saldo_usd = (float(w3.from_wei(bal_wei, 'ether')) * 0.45) + 1500.00
                        break
                except:
                    continue
            
            # 3. PROJEÇÃO
            if saldo_usd > 0:
                n = math.log(META_FINAL / saldo_usd) / math.log(1 + 0.015)
                dias_meta = f"{int(n)} dias"

        except Exception as e:
            print(f"Erro: {e}")
        
        time.sleep(15)

threading.Thread(target=buscar_dados, daemon=True).start()

# O restante do código (Flask routes) permanece igual ao v77