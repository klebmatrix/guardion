import os, requests
from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# CONFIGURAÇÃO
PIN = os.environ.get("guardiao")
WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

def check_network():
    # Testamos 3 fontes diferentes. Se as 3 falharem, o Render está te bloqueando.
    urls = [
        "https://polygon-rpc.com",
        "https://rpc-mainnet.maticvigil.com",
        "https://1rpc.io/matic"
    ]
    
    for url in urls:
        try:
            # Busca POL (Taxas)
            res = requests.post(url, json={"jsonrpc":"2.0","method":"eth_getBalance","params":[WALLET, "latest"],"id":1}, timeout=8)
            if res.status_code == 200:
                data = res.json()
                pol_raw = int(data['result'], 16)
                return f"{pol_raw / 10**18:.4f}", "CONECTADO", url.split('/')[2]
        except Exception as e:
            continue
    return "0.0000", f"BLOQUEIO: {type(e).__name__}", "NENHUM"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('dash'))
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>SISTEMA SNIPER</h1><form method="post"><input type="password" name="pin" autofocus><button type="submit">ENTRAR</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect(url_for('login'))
    
    pol, status, fonte = check_network()
    
    # Simulação do valor que você mencionou para teste de interface
    val_alvo = "14.4459" 

    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:600px; margin:auto; border:1px solid #333; padding:20px; background:#000; border-radius:10px;">
            <h2 style="color:orange; border-bottom:1px solid orange; padding-bottom:10px;">🛡️ TERMINAL v33 - DEBUG</h2>
            
            <div style="background:#111; padding:15px; margin-bottom:15px;">
                <p>STATUS REDE: <b style="color:{'lime' if 'CONECTADO' in status else 'red'};">{status}</b></p>
                <p>FONTE ATUAL: <span style="color:yellow;">{fonte}</span></p>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                <div style="border:1px solid #222; padding:10px;">
                    <small style="color:#666;">SALDO REAL (POL)</small><br>
                    <b style="font-size:20px; color:cyan;">{pol}</b>
                </div>
                <div style="border:1px solid #222; padding:10px;">
                    <small style="color:#666;">VALOR ALVO</small><br>
                    <b style="font-size:20px; color:magenta;">{val_alvo}</b>
                </div>
            </div>

            <p style="font-size:10px; color:#444; margin-top:20px;">DIRETRIZ: Se o saldo for 0.0000, o IP do Render está banido pela Polygon.</p>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)