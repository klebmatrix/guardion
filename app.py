import os, datetime, time, threading, requests, math
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES ESTRATÉGICAS ---
PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00 
DIAS_RESTANTES = 365

logs = []
insights = []
saldo_atual_usd = 1500.00 # Altere para seu saldo real inicial

def calcular_meta_diaria():
    if saldo_atual_usd <= 0: return 0
    # Fórmula de Juros Compostos: M = P(1 + r)^n
    # r = (M/P)^(1/n) - 1
    taxa_necessaria = (math.pow((META_FINAL / saldo_atual_usd), (1 / DIAS_RESTANTES)) - 1) * 100
    return taxa_necessaria

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{t}] {msg}")
    if len(logs) > 12: logs.pop()

def motor_estrategico():
    while True:
        try:
            taxa = calcular_meta_diaria()
            add_log(f"📈 Meta Diária Alvo: {taxa:.2f}%")
            time.sleep(60)
        except:
            pass

threading.Thread(target=motor_estrategico, daemon=True).start()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    
    progresso = (saldo_atual_usd / META_FINAL) * 100
    taxa_alvo = calcular_meta_diaria()
    lucro_hoje_necessario = saldo_atual_usd * (taxa_alvo / 100)
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:'Segoe UI', sans-serif; padding:20px;">
        <div style="max-width:900px; margin:auto; background:#111; border:1px solid #333; padding:25px; border-radius:15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <h1 style="color:#f3ba2f; margin:0 0 20px 0; text-align:center;">🎯 ROTA DO MILHÃO</h1>
            
            <div style="background:#222; border-radius:10px; height:35px; width:100%; margin-bottom:10px; position:relative;">
                <div style="background:linear-gradient(90deg, #f3ba2f, #ffaa00); width:{progresso:.4f}%; height:100%; border-radius:10px; transition:width 1s;"></div>
                <span style="position:absolute; width:100%; text-align:center; top:7px; font-weight:bold; color:#fff;">{progresso:.4f}% DO OBJETIVO</span>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin:25px 0;">
                <div style="background:#1a1a1a; padding:15px; border-radius:10px; border-left:4px solid #f3ba2f;">
                    <span style="color:#888; font-size:12px;">META DIÁRIA NECESSÁRIA</span>
                    <h2 style="margin:5px 0; color:#fff;">{taxa_alvo:.2f}% <small style="font-size:12px; color:lime;">/dia</small></h2>
                </div>
                <div style="background:#1a1a1a; padding:15px; border-radius:10px; border-left:4px solid #00ff00;">
                    <span style="color:#888; font-size:12px;">LUCRO ALVO (PRÓX. 24H)</span>
                    <h2 style="margin:5px 0; color:#fff;">${lucro_hoje_necessario:.2f}</h2>
                </div>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                <div style="background:#0a0a0a; padding:15px; border-radius:10px; height:200px; overflow-y:auto; border:1px solid #222;">
                    <h4 style="margin:0 0 10px 0; color:#f3ba2f;">🧠 Insights da IA</h4>
                    <ul style="padding-left:15px; font-size:13px; color:#ccc;">
                        <li>Agente calculando arbitragem em 2 redes...</li>
                        <li>Monitorando baleias na Binance Home...</li>
                    </ul>
                </div>
                <div style="background:#0a0a0a; padding:15px; border-radius:10px; height:200px; overflow-y:auto; border:1px solid #222;">
                    <h4 style="margin:0 0 10px 0; color:#f3ba2f;">📡 Logs de Operação</h4>
                    <div style="font-size:11px; color:#777; font-family:monospace;">{"<br>".join(logs)}</div>
                </div>
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 30000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect(url_for('index'))
    return '<body style="background:#000;color:#f3ba2f;text-align:center;padding-top:100px;font-family:sans-serif;">' \
           '<h3>🔐 ÁREA DO INVESTIDOR</h3><form method="post"><input type="password" name="pin" style="padding:10px; border-radius:5px; border:none;"><button style="padding:10px 20px; margin-left:10px; border-radius:5px; border:none; background:#f3ba2f; cursor:pointer;">ACESSAR</button></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))