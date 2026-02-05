import os, datetime, json, threading, time, requests
from flask import Flask, request, redirect, url_for, session, send_file
from web3 import Web3
from fpdf import FPDF
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_2026_key")

# --- CONFIGURAÇÕES ---
PIN_SISTEMA = os.environ.get("guardiao", "20262026")
PRIV_KEY = os.environ.get("private_key", "").strip()
if PRIV_KEY and not PRIV_KEY.startswith("0x"): PRIV_KEY = "0x" + PRIV_KEY

WALLET = "0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE"
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Arquivos de estado
BOT_STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

def carregar_dados(arq, padrao):
    if os.path.exists(arq):
        try:
            with open(arq, "r") as f: return json.load(f)
        except: return padrao
    return padrao

def salvar_dados(arq, dados):
    with open(arq, "w") as f: json.dump(dados, f)

def registrar_log(msg, lado="SCAN", res="OK"):
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    logs = carregar_dados(LOGS_FILE, [])
    logs.insert(0, {"data": agora, "mercado": msg, "lado": lado, "resultado": res})
    salvar_dados(LOGS_FILE, logs[:50])

# --- LÓGICA DO SNIPER (Monitorando 2 mercados) ---
def sniper_loop():
    while True:
        state = carregar_dados(BOT_STATE_FILE, {"status": "OFF"})
        if state["status"] == "ON":
            try:
                # 1. Tenta Polymarket
                r_poly = requests.get("https://gamma-api.polymarket.com/events?active=true&limit=5", timeout=10)
                if r_poly.status_code == 200: registrar_log("Vigiando Polymarket", "POLY", "ATIVO")
                
                # 2. Tenta DexSport (Esportes)
                r_dex = requests.get("https://api.dexsport.io/v1/events/active?chainId=137", timeout=10)
                if r_dex.status_code == 200: registrar_log("Vigiando Esportes", "DEX", "ATIVO")
            except:
                registrar_log("Erro de conexão API", "ERRO", "FALHA")
        time.sleep(20)

threading.Thread(target=sniper_loop, daemon=True).start()

# --- INTERFACE HTML (Embutida para matar o 'Not Found') ---
def render_dashboard(state, logs):
    log_rows = "".join([f"<tr><td>{l['data']}</td><td>{l['mercado']}</td><td>{l['lado']}</td><td>{l['resultado']}</td></tr>" for l in logs[:15]])
    cor_status = "#00ff00" if state['status'] == 'ON' else "#ff4b4b"
    
    return f"""
    <html>
    <head><title>SNIPER DASHBOARD</title></head>
    <body style="background:#0e1117; color:white; font-family:sans-serif; text-align:center; padding:20px;">
        <h1 style="color:orange;">🚀 SNIPER GUARDIÃO v3</h1>
        <div style="background:#1a1c24; padding:20px; border-radius:10px; display:inline-block; border:1px solid #333;">
            <p>Status: <b style="color:{cor_status};">{state['status']}</b></p>
            <form action="/toggle" method="post">
                <button name="a" value="ON" style="background:#00ff00; padding:10px; cursor:pointer;">LIGAR</button>
                <button name="a" value="OFF" style="background:#ff4b4b; padding:10px; cursor:pointer;">PARAR</button>
            </form>
            <br>
            <a href="/pdf" style="color:cyan; text-decoration:none;">📥 Gerar Relatório PDF</a>
        </div>
        <div style="margin-top:30px; text-align:left; max-width:800px; margin: 30px auto;">
            <h3>📜 Notícias da Carteira / Logs</h3>
            <table border="1" style="width:100%; border-collapse:collapse; background:#1a1c24;">
                <tr style="background:#333;"><th>Hora</th><th>Mercado</th><th>Lado</th><th>Resultado</th></tr>
                {log_rows}
            </table>
        </div>
        <p style="font-size:10px; color:#555;">Wallet: {WALLET}</p>
    </body>
    </html>
    """

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return '''<body style="background:#000;color:#fff;text-align:center;padding-top:100px;">
              <form method="post"><h2>PIN DE ACESSO:</h2><input type="password" name="pin" style="padding:10px;">
              <button type="submit" style="padding:10px;">ENTRAR</button></form></body>'''

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_dashboard(carregar_dados(BOT_STATE_FILE, {"status": "OFF"}), carregar_dados(LOGS_FILE, []))

@app.post('/toggle')
def toggle():
    if not session.get('logged_in'): return redirect(url_for('login'))
    acao = request.form.get('a')
    salvar_dados(BOT_STATE_FILE, {"status": acao})
    registrar_log(f"Bot alterado para {acao}", "SISTEMA", "OK")
    return redirect(url_for('dashboard'))

@app.route('/pdf')
def pdf():
    if not session.get('logged_in'): return redirect(url_for('login'))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RELATORIO SNIPER - " + WALLET[:10], ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    logs = carregar_dados(LOGS_FILE, [])
    for l in logs[:40]:
        linha = f"{l['data']} | {l['lado']} | {l['mercado']} | {l['resultado']}"
        pdf.cell(0, 8, linha.encode('latin-1', 'replace').decode('latin-1'), ln=True, border=1)
    
    out = BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin-1', 'replace')
    out.write(pdf_content)
    out.seek(0)
    return send_file(out, mimetype='application/pdf', as_attachment=True, download_name="relatorio.pdf")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))