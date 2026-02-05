import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# CONFIGURAÇÃO FIXA
PIN = os.environ.get("guardiao")
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

# CACHE DE DADOS
cache = {"pol": "SINCRO...", "usdc": "SINCRO...", "status": "OFFLINE"}

def motor_resgate():
    while True:
        try:
            # Tenta via Node Público Cloudflare (Mais estável que Polygonscan p/ Render)
            rpc = "https://polygon-rpc.com"
            
            # POL
            req_pol = requests.post(rpc, json={"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}, timeout=10).json()
            if 'result' in req_pol:
                cache["pol"] = f"{int(req_pol['result'], 16) / 10**18:.4f}"
            
            # USDC
            data_hex = "0x70a08231000000000000000000000000" + WALLET[2:]
            req_usdc = requests.post(rpc, json={"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_CONTRACT,"data":data_hex},"latest"],"id":1}, timeout=10).json()
            if 'result' in req_usdc:
                cache["usdc"] = f"{int(req_usdc['result'], 16) / 10**6:.2f}"
            
            cache["status"] = "ONLINE"
        except:
            cache["status"] = "ERRO_RPC"
        time.sleep(15)

threading.Thread(target=motor_resgate, daemon=True).start()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<h1>LOGIN SNIPER</h1><form method="post"><input type="password" name="pin" autofocus><button>ENTRAR</button></form>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect('/login')
    return f"""
    <body style="background:#000; color:#0f0; font-family:monospace; padding:30px;">
        <div style="border:1px solid #333; padding:20px; max-width:500px; margin:auto;">
            <h2 style="color:orange;">⚡ SNIPER TERMINAL v31</h2>
            <hr>
            <p>STATUS: <b>{cache['status']}</b></p>
            <p>POL: <span style="color:white;">{cache['pol']}</span></p>
            <p>USDC: <span style="color:white;">{cache['usdc']}</span></p>
            <hr>
            <p style="font-size:10px; color:#555;">WALLET: {WALLET}</p>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)