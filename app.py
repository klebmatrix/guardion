import os, datetime, time, threading
from flask import Flask, session, redirect, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO DE COMBATE ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# CONFIGURAÇÃO DE TRADE (Ajuste aqui)
ALVO_COMPRA = 14.4459
STOP_LOSS = 14.0500    # Vende tudo se cair aqui para não quebrar
TAKE_PROFIT = 14.7500  # Vende tudo aqui para botar o lucro no bolso

logs = []
def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def motor_autonomo():
    add_log("🤖 SISTEMA INTEGRAL ATIVADO")
    # Estado inicial: se saldo POL for baixo, assume que já comprou (está em USDC)
    posicao_comprada = True if w3.eth.get_balance(WALLET) < w3.to_wei(2, 'ether') else False
    
    while True:
        try:
            # 1. PEGAR PREÇO REAL (Substitua pela sua fonte de dados/API)
            preco_atual = 14.2100 # Exemplo do preço que você me deu
            
            if not posicao_comprada:
                # LÓGICA DE ENTRADA
                if preco_atual <= ALVO_COMPRA:
                    add_log(f"🎯 ALVO DE COMPRA! Executando Swap POL -> USDC...")
                    # [Função de Swap real aqui]
                    posicao_comprada = True
            else:
                # LÓGICA DE SAÍDA (O que faltou antes!)
                if preco_atual >= TAKE_PROFIT:
                    add_log(f"💰 LUCRO ATINGIDO! Vendendo USDC -> POL...")
                    # [Função de Venda real aqui]
                    posicao_comprada = False
                
                elif preco_atual <= STOP_LOSS:
                    add_log(f"🚨 STOP LOSS! Saindo para proteger o que restou...")
                    # [Função de Venda real aqui]
                    posicao_comprada = False
            
            add_log(f"📊 Monitorando: {preco_atual} | Status: {'Em Trade' if posicao_comprada else 'Aguardando'}")

        except Exception as e:
            add_log(f"❌ Erro: {str(e)[:25]}")
        
        time.sleep(10)

threading.Thread(target=motor_autonomo, daemon=True).start()

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect('/login')
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs[:12]])
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:2px solid orange; padding:20px; background:#000;">
            <h2 style="color:orange;">🛡️ SNIPER AUTÔNOMO v45</h2>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:20px;">
                <div style="background:#111; padding:10px; border-left:4px solid magenta;">
                    ALVO COMPRA: <b>{ALVO_COMPRA}</b>
                </div>
                <div style="background:#111; padding:10px; border-left:4px solid lime;">
                    META LUCRO: <b>{TAKE_PROFIT}</b>
                </div>
            </div>
            <div style="background:#0a0a0a; height:300px; overflow-y:auto; padding:10px; font-size:12px; color:#888;">
                {log_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 8000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<h1>LOGIN</h1><form method="post"><input type="password" name="pin" autofocus><button>ENTRAR</button></form>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)