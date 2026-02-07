import os, sys
from flask import Flask, request, redirect, url_for, session
from web3 import Web3
from eth_account import Account

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "diagnostico_v87")

# Configurações de Ambiente
PIN_SISTEMA = os.environ.get("guardiao", "123456")
RPC_URL = "https://polygon-rpc.com"

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        mod_html = ""
        
        # Tenta carregar as chaves com segurança
        for i in range(1, 4):
            key = os.environ.get(f"KEY_MOD_{i}")
            if key:
                acc = Account.from_key(key)
                # Fallback se a rede falhar
                try:
                    pol = w3.eth.get_balance(acc.address) / 10**18
                except:
                    pol = 0.0
                
                mod_html += f"""
                <div style="background:#161b22; padding:10px; border-radius:8px; margin-bottom:10px; border:1px solid #333;">
                    <b style="color:#58a6ff;">MOD_0{i}</b><br>
                    <small style="color:gray;">{acc.address}</small><br>
                    <b style="color:lime;">POL: {pol:.2f}</b>
                </div>"""
                
        return f"""
        <body style="background:#0d1117; color:#c9d1d9; font-family:sans-serif; padding:20px;">
            <h3>OMNI v87.2 - SISTEMA ATIVO</h3>
            {mod_html if mod_html else "<p>Nenhuma KEY_MOD_X configurada no Render.</p>"}
        </body>"""
    
    except Exception as e:
        # Se der erro, ele mostra o texto do erro na tela
        return f"<h1>ERRO DE DIAGNÓSTICO:</h1><p>{str(e)}</p>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '<body style="background:#000;color:cyan;text-align:center;padding-top:100px;">' \
           '<h3>PAINEL OMNI</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))