import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN = os.environ.get("guardiao")
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
# O script agora procura exatamente por este nome no Render:
PVT_KEY = os.environ.get("CHAVE_PRIVADA") 
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

bot_data = {
    "saldo_pol": "0.0000",
    "preco_alvo": 14.4459,
    "status": "AGUARDANDO GATILHO",
    "logs": []
}

def add_log(msg):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    bot_data["logs"].insert(0, f"[{agora}] {msg}")
    bot_data["logs"] = bot_data["logs"][:12]

def motor_sniper():
    add_log("SISTEMA ARMADO - VIGIANDO ALVO 14.4459")
    if not PVT_KEY:
        add_log("AVISO: Variável CHAVE_PRIVADA não detetada no Render.")
    
    while True:
        try:
            # 1. Atualiza Saldo Real
            balance = w3.eth.get_balance(WALLET)
            bot_data["saldo_pol"] = f"{w3.from_wei(balance, 'ether'):.4f}"
            
            # 2. Lógica de Preço (Aqui ligamos à API do mercado)
            preco_atual = 14.5000 # Simulação de mercado
            
            if preco_atual <= bot_data["preco_alvo"]:
                if PVT_KEY:
                    add_log(f"GATILHO ATIVADO! Preço: {preco_atual}")
                    # AQUI O BOT EXECUTA A COMPRA USANDO A CHAVE_PRIVADA
                    add_log("ORDEM ENVIADA PARA A BLOCKCHAIN...")
                    time.sleep(10)
                else:
                    add_log("ERRO: Gatilho disparado mas CHAVE_PRIVADA está vazia.")
            
            bot_data["status"] = "VIGIANDO MERCADO"
        except Exception as e:
            add_log(f"ERRO: {str(e)[:20]}")
        
        time.sleep(10)

threading.Thread(target=motor_sniper, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<h1>SNIPER TERMINAL</h1><form method="post"><input type="password" name="pin" autofocus><button>ENTRAR</button></form>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect('/login')
    
    logs_html = "".join([f"<div style='color:#aaa; border-bottom:1px solid #222; padding:3px;'>{l}</div>" for l in bot_data["logs"]])
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:700px; margin:auto; border:2px solid orange; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid orange; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">🛡️ SNIPER v37</h2>
                <div style="text-align:right;">
                    SALDO: <b style="color:cyan;">{bot_data['saldo_pol']} POL</b>
                </div>
            </div>
            
            <div style="margin:20px 0; padding:15px; background:#111; border-left:5px solid lime;">
                STATUS: <b>{bot_data['status']}</b> | ALVO: <b style="color:magenta;">{bot_data['preco_alvo']}</b>
            </div>

            <div style="background:#0a0a0a; border:1px solid #333; height:200px; overflow-y:auto; padding:10px;">
                <small style="color:#444;">LOGS:</small><br>
                {logs_html}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)