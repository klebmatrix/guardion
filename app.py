import os, datetime, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO ---
PIN = os.environ.get("guardiao")
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
PVT_KEY = os.environ.get("CHAVE_PRIVADA") 
RPC_URL = "https://polygon-rpc.com"

def obter_saldo_real():
    try:
        payload = {"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}
        res = requests.post(RPC_URL, json=payload, timeout=8).json()
        if 'result' in res:
            valor_wei = int(res['result'], 16)
            return f"{valor_wei / 10**18:.4f}"
    except:
        return "ERRO_RPC"
    return "0.0000"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>LOGIN TERMINAL</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">ENTRAR</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect('/login')
    
    # Busca o saldo NO MOMENTO do acesso
    saldo_atual = obter_saldo_real()
    alvo = 14.4459
    status = "PRONTO PARA OPERAR" if PVT_KEY else "AVISO: SEM CHAVE_PRIVADA"

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:600px; margin:auto; border:2px solid orange; padding:20px; background:#000; border-radius:8px;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px; margin-bottom:20px;">
                <h2 style="color:orange; margin:0;">🛡️ SNIPER v39</h2>
                <div style="text-align:right;">
                    SALDO: <b style="color:cyan; font-size:20px;">{saldo_atual} POL</b>
                </div>
            </div>
            
            <div style="padding:15px; background:#111; border-left:5px solid {'lime' if PVT_KEY else 'red'}; margin-bottom:20px;">
                <b>STATUS:</b> {status}<br>
                <b>ALVO ATUAL:</b> <span style="color:magenta;">{alvo}</span>
            </div>

            <div style="background:#0a0a0a; border:1px solid #333; padding:15px; color:#666; font-size:12px;">
                <p>• Carteira: {WALLET}</p>
                <p>• Transações: Assinatura via CHAVE_PRIVADA</p>
                <p>• Rede: Polygon Mainnet (RPC Cloudflare)</p>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)