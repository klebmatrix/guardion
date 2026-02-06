import os, datetime, time, threading, requests
from flask import Flask, session, redirect, url_for, request

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES ---
PIN = os.environ.get("guardiao", "1234")
status_baleias = "🛡️ MONITORANDO FLUXO"
sentimento_mercado = "NEUTRO"

logs = []
def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{t}] {msg}")
    if len(logs) > 8: logs.pop()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:sans-serif; padding:20px;">
        <div style="max-width:1000px; margin:auto;">
            <h1 style="color:#f3ba2f; border-bottom:1px solid #222; padding-bottom:10px;">🏰 AGENTE FORTRESS v66</h1>
            
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:15px; margin-bottom:25px;">
                <div style="background:#111; padding:15px; border-radius:10px; border-top:3px solid #00d4ff;">
                    <small style="color:#888;">WHALE TRACKER</small>
                    <div style="font-weight:bold; margin-top:5px;">{status_baleias}</div>
                </div>
                <div style="background:#111; padding:15px; border-radius:10px; border-top:3px solid #ff0055;">
                    <small style="color:#888;">TRAILING STOP</small>
                    <div style="font-weight:bold; margin-top:5px; color:lime;">ATIVO (Gatilho 2.5%)</div>
                </div>
                <div style="background:#111; padding:15px; border-radius:10px; border-top:3px solid #f3ba2f;">
                    <small style="color:#888;">SENTIMENTO GLOBAL</small>
                    <div style="font-weight:bold; margin-top:5px;">{sentimento_mercado}</div>
                </div>
            </div>

            <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #222;">
                <h3 style="margin-top:0; color:#f3ba2f;">📡 Monitor de Redes & Fluxo</h3>
                <div style="font-family:monospace; color:#888;">
                    {"<br>".join(logs) if logs else "Sincronizando sensores de baleias..."}
                </div>
            </div>
            
            <div style="margin-top:20px; text-align:center;">
                <button onclick="alert('Modo de Segurança Ativado!')" style="background:#ff0055; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">🚨 BOTÃO DE PÂNICO (EXIT ALL)</button>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 20000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000;color:#f3ba2f;text-align:center;padding-top:100px;"><h3>ACESSO OMNI</h3><form method="post"><input type="password" name="pin" autofocus></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))