import os
import io
import json
import time
import math
import datetime
import threading
import requests
import qrcode
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from web3 import Web3
from fpdf import FPDF

# --- INICIALIZAÇÃO FLASK ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-secreta-omni-2026")

# --- CONFIGURAÇÕES DE SEGURANÇA ---
ADMIN_USER = os.environ.get("USER_LOGIN", "admin")
ADMIN_PASS = os.environ.get("USER_PASS", "1234")

# --- MÓDULOS E CARTEIRAS ---
MODULOS = {
    "MOD_01": os.environ.get("WALLET_01", "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"),
    "MOD_02": os.environ.get("WALLET_02", "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"),
    "MOD_03": os.environ.get("WALLET_03", "0x0000000000000000000000000000000000000000")
}

META_FINAL = 1000000.00

# --- ESTADO GLOBAL (PERSISTÊNCIA) ---
STATE_FILE = "omni_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(data):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

# Estado inicial
estado_global = {
    "saldos": {},
    "precos": {"BTC": 65000.0, "ETH": 3500.0},
    "ultima_atualizacao": datetime.datetime.now().isoformat(),
    "status": "ATIVO"
}

# --- MOTOR DE DADOS (THREAD INFINITA) ---
def motor_dados_infinito():
    while True:
        try:
            # 1. Atualizar Preços (Coindesk para BTC)
            try:
                r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10).json()
                estado_global["precos"]["BTC"] = float(r['bpi']['USD']['rate_float'])
            except:
                pass

            # 2. Atualizar Preço ETH (CoinGecko)
            try:
                r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=10).json()
                estado_global["precos"]["ETH"] = float(r['ethereum']['usd'])
            except:
                pass

            # 3. Atualizar Saldos de Cada Módulo
            for mod_name, wallet in MODULOS.items():
                if wallet and wallet != "0x0000000000000000000000000000000000000000":
                    try:
                        w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/polygon"))
                        bal_wei = w3.eth.get_balance(wallet)
                        bal_native = float(w3.from_wei(bal_wei, 'ether'))
                        estado_global["saldos"][mod_name] = {
                            "saldo_matic": bal_native,
                            "saldo_usd": bal_native * 0.40,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    except:
                        pass

            estado_global["ultima_atualizacao"] = datetime.datetime.now().isoformat()
            estado_global["status"] = "ATIVO"
            save_state(estado_global)

        except Exception as e:
            estado_global["status"] = f"ERRO: {str(e)[:50]}"

        # Aguarda 20 segundos antes de atualizar novamente
        time.sleep(20)

# --- AUTO-PING (EVITA HIBERNAÇÃO NO RENDER) ---
def auto_ping():
    while True:
        try:
            time.sleep(600)  # A cada 10 minutos
            # Faz uma requisição interna para manter o app ativo
            requests.get(f"http://localhost:{os.environ.get('PORT', 10000)}/status", timeout=5)
        except:
            pass

# --- INICIAR THREADS ---
if not any(t.name == "MotorDados" for t in threading.enumerate()):
    threading.Thread(target=motor_dados_infinito, name="MotorDados", daemon=True).start()

if not any(t.name == "AutoPing" for t in threading.enumerate()):
    threading.Thread(target=auto_ping, name="AutoPing", daemon=True).start()

# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username', '')
        pwd = request.form.get('password', '')
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        return '''
        <body style="background:#000; color:#f3ba2f; text-align:center; padding-top:100px; font-family:sans-serif;">
            <h2>OMNI v78 - Acesso Negado</h2>
            <p>Credenciais inválidas. Tente novamente.</p>
            <a href="/login" style="color:#f3ba2f;">← Voltar</a>
        </body>
        '''
    return '''
    <body style="background:#000; color:#f3ba2f; text-align:center; padding-top:100px; font-family:sans-serif;">
        <div style="max-width:300px; margin:auto; background:#0a0a0a; padding:30px; border-radius:15px; border:1px solid #333;">
            <h1 style="margin:0;">OMNI v78</h1>
            <form method="post" style="margin-top:30px;">
                <input type="text" name="username" placeholder="Usuário" required style="width:100%; padding:10px; margin:10px 0; border:1px solid #333; background:#111; color:#f3ba2f;">
                <input type="password" name="password" placeholder="Senha" required style="width:100%; padding:10px; margin:10px 0; border:1px solid #333; background:#111; color:#f3ba2f;">
                <button type="submit" style="width:100%; padding:10px; background:#f3ba2f; color:#000; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">ENTRAR</button>
            </form>
        </div>
    </body>
    '''

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    estado = load_state()
    saldo_total = sum([v.get("saldo_usd", 0) for v in estado.get("saldos", {}).values()]) + 1500
    progresso = (saldo_total / META_FINAL) * 100
    
    try:
        n = math.log(META_FINAL / saldo_total) / math.log(1.015)
        dias_meta = f"{int(n)} dias"
    except:
        dias_meta = "∞ dias"
    
    return f'''
    <body style="background:#000; color:#eee; font-family:sans-serif; padding:30px;">
        <div style="max-width:900px; margin:auto;">
            <h1 style="color:#f3ba2f; text-align:center;">OMNI v78 - DASHBOARD</h1>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin:30px 0;">
                <div style="background:#0a0a0a; border:1px solid #333; padding:20px; border-radius:15px;">
                    <h3 style="color:#f3ba2f; margin:0;">SALDO TOTAL</h3>
                    <h2 style="font-size:40px; margin:10px 0;">${saldo_total:,.2f}</h2>
                    <small style="color:#888;">Atualizado: {estado.get("ultima_atualizacao", "...")}</small>
                </div>
                
                <div style="background:#0a0a0a; border:1px solid #333; padding:20px; border-radius:15px;">
                    <h3 style="color:#f3ba2f; margin:0;">PREÇOS</h3>
                    <p style="margin:5px 0;">BTC: ${estado.get("precos", {}).get("BTC", 0):,.2f}</p>
                    <p style="margin:5px 0;">ETH: ${estado.get("precos", {}).get("ETH", 0):,.2f}</p>
                </div>
            </div>
            
            <div style="background:#0a0a0a; border:1px solid #333; padding:20px; border-radius:15px; margin:20px 0;">
                <h3 style="color:#f3ba2f;">PROJEÇÃO 1 MILHÃO</h3>
                <h2 style="color:#f3ba2f; margin:10px 0;">{dias_meta}</h2>
                <div style="background:#111; height:15px; border-radius:10px; overflow:hidden;">
                    <div style="background:linear-gradient(90deg, #f3ba2f, #00ff00); width:{progresso}%; height:100%;"></div>
                </div>
                <small style="color:#888;">Progresso: {progresso:.1f}%</small>
            </div>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin:20px 0;">
                <a href="/relatorio_pdf" style="background:#007bff; color:white; padding:15px; text-align:center; border-radius:10px; text-decoration:none; font-weight:bold;">📥 BAIXAR RELATÓRIO PDF</a>
                <a href="/logout" style="background:#dc3545; color:white; padding:15px; text-align:center; border-radius:10px; text-decoration:none; font-weight:bold;">🚪 SAIR</a>
            </div>
        </div>
    </body>
    '''

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/status')
def status():
    return jsonify({"status": "ATIVO", "timestamp": datetime.datetime.now().isoformat()})

@app.route('/relatorio_pdf')
def relatorio_pdf():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    estado = load_state()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "OMNI v78 - RELATÓRIO PROFISSIONAL", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.cell(0, 10, f"Status: {estado.get('status', 'DESCONHECIDO')}", ln=True)
    pdf.ln(5)
    
    saldo_total = sum([v.get("saldo_usd", 0) for v in estado.get("saldos", {}).values()]) + 1500
    pdf.cell(0, 10, f"Saldo Total: ${saldo_total:,.2f}", ln=True)
    pdf.cell(0, 10, f"BTC: ${estado.get('precos', {}).get('BTC', 0):,.2f}", ln=True)
    pdf.cell(0, 10, f"ETH: ${estado.get('precos', {}).get('ETH', 0):,.2f}", ln=True)
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"omni_relatorio_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
