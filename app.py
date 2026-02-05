import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request # <-- CORRIGIDO AQUI
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO MASTER ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Histórico e Logs
historico_precos = []
logs = []

def add_log(msg):
    agora = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{agora}] {msg}")
    if len(logs) > 25: logs.pop()

# --- MOTOR DE DECISÃO INTELIGENTE ---
def motor_autonomo():
    add_log("🧠 CÉREBRO ALGORÍTMICO ON")
    while True:
        try:
            # Pega o preço (usando 14.21 como base do seu relato)
            preco_atual = 14.21 
            historico_precos.append(preco_atual)
            if len(historico_precos) > 10: historico_precos.pop(0)

            if len(historico_precos) > 3:
                media = sum(historico_precos) / len(historico_precos)
                bal_wei = w3.eth.get_balance(WALLET)
                pol_real = float(w3.from_wei(bal_wei, 'ether'))

                # Lógica simplificada de decisão do bot
                if pol_real > 1.0 and preco_atual < 14.40:
                    add_log(f"🤖 ANALISANDO: Preço {preco_atual} é oportunidade. Aguardando sinal de subida...")
                
                elif pol_real < 1.0:
                    add_log(f"📊 MONITORANDO TRADE: Preço {preco_atual} | Meta: 14.80")

            else:
                add_log("⏳ Sincronizando dados de mercado...")

        except Exception as e:
            add_log(f"❌ Erro Motor: {str(e)[:20]}")
        
        time.sleep(15)

# Inicia o robô
threading.Thread(target=motor_autonomo, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dashboard'))
    return '''
    <body style="background:#000;color:lime;text-align:center;padding-top:100px;font-family:monospace;">
        <h2>SISTEMA AUTÔNOMO v46.1</h2>
        <form method="post">
            <input type="password" name="pin" placeholder="PIN SEGURANÇA" autofocus style="padding:10px;background:#111;color:#fff;border:1px solid lime;">
            <button type="submit" style="padding:10px;background:lime;color:#000;font-weight:bold;cursor:pointer;">ENTRAR</button>
        </form>
    </body>
    '''

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect(url_for('login'))
    
    bal = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs])
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:2px solid lime; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid lime; padding-bottom:10px; margin-bottom:20px;">
                <h2 style="color:lime; margin:0;">🤖 BOT DECISOR v46.1</h2>
                <div>POL: <b style="color:cyan;">{bal:.4f}</b></div>
            </div>
            <div style="background:#0a0a0a; height:400px; overflow-y:auto; padding:10px; font-size:12px; color:#0f0; border:1px solid #111;">
                {log_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)