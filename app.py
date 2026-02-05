import os, datetime, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# CONFIGURAÇÃO
PIN = os.environ.get("guardiao")
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

def buscar_saldos():
    # Tentativa de conexão direta via RPC da Cloudflare
    rpc = "https://polygon-rpc.com"
    try:
        # Busca POL
        r1 = requests.post(rpc, json={"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}, timeout=5).json()
        pol = f"{int(r1['result'], 16) / 10**18:.4f}"
        
        # Busca USDC
        hex_data = "0x70a08231000000000000000000000000" + WALLET[2:]
        r2 = requests.post(rpc, json={"jsonrpc":"2.0","method":"eth_call","params":[{"to":USDC_CONTRACT,"data":hex_data},"latest"],"id":1}, timeout=5).json()
        usdc = f"{int(r2['result'], 16) / 10**6:.2f}"
        
        return pol, usdc, "CONECTADO"
    except Exception as e:
        return "0.0000", "0.00", f"ERRO: {str(e)[:20]}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dash'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>SNIPER LOGIN</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">ENTRAR</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect(url_for('login'))
    
    # Busca os dados em tempo real no refresh
    pol, usdc, status = buscar_saldos()
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:500px; margin:auto; border:1px solid #333; padding:20px; background:#000;">
            <h2 style="color:orange;">⚡ SNIPER TERMINAL v32</h2>
            <hr style="border:0; border-top:1px solid #333;">
            <p>STATUS: <b style="color:{'lime' if 'CONECTADO' in status else 'red'};">{status}</b></p>
            <p>POL: <b style="color:cyan;">{pol}</b></p>
            <p>USDC: <b style="color:lime;">{usdc}</b></p>
            <hr style="border:0; border-top:1px solid #333;">
            <p style="font-size:10px; color:#444;">ID: {WALLET}</p>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)