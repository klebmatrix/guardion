import os, datetime, requests, time
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN = os.environ.get("guardiao")
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PVT_KEY = os.environ.get("CHAVE_PRIVADA") 
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Memória temporária de logs
logs_sniper = []

def add_log(msg):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs_sniper.insert(0, f"[{agora}] {msg}")

def executar_compra():
    if not PVT_KEY:
        return "ERRO: SEM CHAVE"
    try:
        # Aqui o bot monta a transação de Swap (Exemplo simplificado de envio de POL)
        nonce = w3.eth.get_transaction_count(WALLET)
        tx = {
            'nonce': nonce,
            'to': '0x...ENDEREÇO_DO_CONTRATO_ALVO...', 
            'value': w3.to_wei(0.1, 'ether'), # Exemplo: compra usando 0.1 POL
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 137
        }
        signed_tx = w3.eth.account.sign_transaction(tx, PVT_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return f"SUCESSO: {w3.to_hex(tx_hash)[:15]}..."
    except Exception as e:
        return f"FALHA: {str(e)[:20]}"

def obter_dados():
    try:
        balance = w3.eth.get_balance(WALLET)
        saldo = f"{w3.from_wei(balance, 'ether'):.4f}"
        # Simulando preço do alvo (Aqui ligaríamos à API da Polymarket/DEX)
        preco_atual = 14.5000 
        return saldo, preco_atual
    except:
        return "0.0000", 0.0

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>SNIPER LOGIN</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">ENTRAR</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect('/login')
    
    saldo, preco = obter_dados()
    alvo = 14.4459
    
    # Lógica de Gatilho Automático
    status_bot = "VIGIANDO"
    if preco <= alvo and PVT_KEY:
        res = executar_compra()
        add_log(f"GATILHO ACIONADO! {res}")
        status_bot = "EXECUTANDO..."

    logs_render = "".join([f"<div style='color:#666; font-size:12px; border-bottom:1px solid #111;'>{l}</div>" for l in logs_sniper[:5]])

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:600px; margin:auto; border:2px solid orange; padding:20px; background:#000; border-radius:8px;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px; margin-bottom:20px;">
                <h2 style="color:orange; margin:0;">🛡️ SNIPER v40 - FULL</h2>
                <div style="text-align:right;">
                    SALDO: <b style="color:cyan; font-size:20px;">{saldo} POL</b>
                </div>
            </div>
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:20px;">
                <div style="background:#111; padding:15px; border-left:4px solid lime;">
                    STATUS: <br><b>{status_bot}</b>
                </div>
                <div style="background:#111; padding:15px; border-left:4px solid magenta;">
                    ALVO: <br><b>{alvo}</b>
                </div>
            </div>

            <div style="background:#0a0a0a; border:1px solid #222; padding:10px; min-height:100px;">
                <small style="color:#444;">LOGS DE EXECUÇÃO:</small><br>
                {logs_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 5000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)