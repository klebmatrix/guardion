import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN = os.environ.get("guardiao")
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PVT_KEY = os.environ.get("CHAVE_PRIVADA") 
RPC_URL = "https://polygon-rpc.com"

bot_data = {
    "saldo_pol": "SINCRO...",
    "preco_alvo": 14.4459,
    "status": "CONECTANDO...",
    "logs": []
}

def add_log(msg):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    bot_data["logs"].insert(0, f"[{agora}] {msg}")
    bot_data["logs"] = bot_data["logs"][:12]

def motor_sniper():
    add_log("MOTOR REINICIADO - MODO COMPATIBILIDADE")
    
    while True:
        try:
            # BUSCA SALDO POL (MÉTODO REQUESTS - O ÚNICO QUE FUNCIONOU NO SEU RENDER)
            payload = {"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}
            res = requests.post(RPC_URL, json=payload, timeout=10).json()
            
            if 'result' in res:
                saldo_hex = res['result']
                saldo_final = int(saldo_hex, 16) / 10**18
                bot_data["saldo_pol"] = f"{saldo_final:.4f}"
                bot_data["status"] = "VIGIANDO MERCADO"
            else:
                bot_data["status"] = "ERRO NA RESPOSTA RPC"

            # Lógica de Gatilho
            if not PVT_KEY:
                if "AVISO" not in str(bot_data["logs"]):
                    add_log("AVISO: CHAVE_PRIVADA NÃO ENCONTRADA NO RENDER")

        except Exception as e:
            bot_data["status"] = "ERRO DE CONEXÃO"
            add_log(f"FALHA: {str(e)[:20]}")
        
        time.sleep(12)

threading.Thread(target=motor_sniper, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>TERMINAL SNIPER</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">ENTRAR</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect('/login')
    
    logs_html = "".join([f"<div style='color:#888; border-bottom:1px solid #222; padding:3px;'>{l}</div>" for l in bot_data["logs"]])
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:600px; margin:auto; border:2px solid orange; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid orange; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">🛡️ SNIPER v38</h2>
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