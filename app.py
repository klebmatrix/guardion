import os, datetime, time, threading, requests, math
from flask import Flask, session, redirect, url_for, request
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(32)

# --- CONFIGURAÇÕES ---
PIN = os.environ.get("guardiao", "1234")
META_FINAL = 1000000.00 
saldo_atual_usd = 1500.00

# ALOCAÇÃO ALVO (O Agente tentará manter essas porcentagens)
ALOCACAO_ALVO = {
    "BTC": 50,  # 50% em Ouro Digital
    "ETH": 25,  # 25% em Tecnologia
    "ALT": 15,  # 15% em Ativos de Crescimento (BNB/POL)
    "CASH": 10  # 10% em Dólar (Reserva de Oportunidade)
}

logs = []

def add_log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    logs.insert(0, f"[{t}] {msg}")
    if len(logs) > 10: logs.pop()

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    
    progresso = (saldo_atual_usd / META_FINAL) * 100
    
    # Gerar HTML da Tabela de Alocação
    aloc_html = ""
    for ativo, porcentagem in ALOCACAO_ALVO.items():
        cor = "#f3ba2f" if ativo == "BTC" else "#627eea" if ativo == "ETH" else "#00ff00"
        aloc_html += f"""
        <div style="margin-bottom:15px;">
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:5px;">
                <span>{ativo}</span><span>{porcentagem}%</span>
            </div>
            <div style="background:#222; height:8px; border-radius:5px;">
                <div style="background:{cor}; width:{porcentagem}%; height:100%; border-radius:5px;"></div>
            </div>
        </div>"""

    return f"""
    <body style="background:#0a0a0a; color:#eee; font-family:'Inter', sans-serif; padding:20px;">
        <div style="max-width:1000px; margin:auto;">
            <header style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px;">
                <h2 style="color:#f3ba2f; margin:0;">🛡️ OMNI COMMAND CENTER <small style="color:#666; font-size:12px;">v65</small></h2>
                <div style="text-align:right;">
                    <span style="display:block; font-size:10px; color:#888;">STATUS DO AGENTE</span>
                    <span style="color:lime; font-weight:bold;">● EXECUTANDO REBALANCEAMENTO</span>
                </div>
            </header>

            <div style="display:grid; grid-template-columns: 2fr 1fr; gap:20px;">
                <div>
                    <div style="background:#111; padding:20px; border-radius:12px; border:1px solid #222; margin-bottom:20px;">
                        <h4 style="margin:0 0 15px 0;">Progresso para 1 Milhão</h4>
                        <div style="background:#222; height:30px; border-radius:8px; position:relative; overflow:hidden;">
                            <div style="background:linear-gradient(90deg, #f3ba2f, #ffcc00); width:{progresso:.4f}%; height:100%;"></div>
                            <span style="position:absolute; width:100%; text-align:center; top:6px; font-weight:bold; font-size:14px; color:#fff;">{progresso:.4f}%</span>
                        </div>
                    </div>
                    
                    <div style="background:#111; padding:20px; border-radius:12px; border:1px solid #222;">
                        <h4 style="margin:0 0 15px 0;">Histórico de Operações</h4>
                        <div style="font-family:monospace; font-size:11px; color:#888; line-height:1.6;">
                            {"<br>".join(logs) if logs else "Aguardando sinais do mercado..."}
                        </div>
                    </div>
                </div>

                <div style="background:#111; padding:20px; border-radius:12px; border:1px solid #222; height:fit-content;">
                    <h4 style="margin:0 0 20px 0; color:#f3ba2f;">📊 Estratégia de Carteira</h4>
                    {aloc_html}
                    <hr style="border:0; border-top:1px solid #222; margin:20px 0;">
                    <p style="font-size:11px; color:#666; font-style:italic;">
                        O Agente rebalanceia automaticamente quando um ativo desvia mais de 5% da meta.
                    </p>
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
    return '<body style="background:#000;color:#f3ba2f;text-align:center;padding-top:100px;">' \
           '<h3>DASHBOARD DE ELITE</h3><form method="post"><input type="password" name="pin" autofocus><button>ENTRAR</button></form></body>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))