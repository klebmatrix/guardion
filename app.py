import os
import datetime
import json
import threading
import time
import requests
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from web3 import Web3
from fpdf import FPDF
from io import BytesIO

# --- CONFIGURAÇÕES DE AMBIENTE ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sniper_ultra_2026_secure_key")

# PIN de acesso e Chave Privada (Configurar no Render)
PIN_SISTEMA = os.environ.get("guardiao", "123456")
PRIV_KEY = os.environ.get("private_key")

# --- BLOCKCHAIN SETUP ---
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
CARTEIRA_ALVO = web3.to_checksum_address("0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E")

# --- PERSISTÊNCIA DE DADOS ---
BOT_STATE_FILE = "bot_state.json"
LOGS_FILE = "logs.json"

def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def registrar_log(mensagem, lado="AUTO", resultado="OK"):
    agora = datetime.datetime.now().strftime("%d/%m %H:%M:%S")
    log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": resultado}
    logs = load_json(LOGS_FILE, [])
    logs.insert(0, log)
    save_json(LOGS_FILE, logs[:100])

# --- LÓGICA DO BOT (THREAD SEPARADA) ---
def sniper_loop():
    while True:
        state = load_json(BOT_STATE_FILE, {"status": "OFF", "preference": "YES"})
        if state["status"] == "ON" and PRIV_KEY:
            # Simulação de monitoramento
            pass
        time.sleep(60)

# Inicia o bot em background apenas uma vez
if not any(t.name == "SniperBotThread" for t in threading.enumerate()):
    threading.Thread(target=sniper_loop, name="SniperBotThread", daemon=True).start()

# --- MOTOR DE PDF ---
class PDFReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "SNIPER BOT - RELATÓRIO DE OPERAÇÕES", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

def gerar_pdf_bytes():
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, f"Data de Emissão: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.cell(0, 10, f"Carteira Monitorada: {CARTEIRA_ALVO}", ln=True)
    pdf.ln(5)

    logs = load_json(LOGS_FILE, [])
    
    # Cabeçalho da Tabela
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 10, "Data/Hora", 1, 0, "C", True)
    pdf.cell(80, 10, "Operação", 1, 0, "C", True)
    pdf.cell(30, 10, "Lado", 1, 0, "C", True)
    pdf.cell(40, 10, "Status", 1, 1, "C", True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    for log in logs[:30]:
        pdf.cell(40, 10, log.get('data', ''), 1)
        pdf.cell(80, 10, str(log.get('mercado', ''))[:35], 1)
        pdf.cell(30, 10, log.get('lado', ''), 1)
        pdf.cell(40, 10, log.get('resultado', ''), 1, 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- ROTAS DO DASHBOARD ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == PIN_SISTEMA:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return "Acesso Negado: PIN Inválido", 403
    return '''
    <body style="background:#0e1117; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh;">
        <form method="post" style="background:#1a1c24; padding:40px; border-radius:15px; box-shadow: 0 0 20px rgba(0,255,255,0.2); text-align:center;">
            <h2 style="color:#00f2ff;">⚡ Sniper Bot Login</h2>
            <input type="password" name="pin" placeholder="Digite seu PIN" required style="padding:12px; width:100%; margin:20px 0; border-radius:5px; border:none;">
            <br>
            <button type="submit" style="background:#00f2ff; color:black; border:none; padding:12px 30px; border-radius:5px; cursor:pointer; font-weight:bold;">ENTRAR</button>
        </form>
    </body>
    '''

@app.route('/')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    state = load_json(BOT_STATE_FILE, {"status": "OFF", "preference": "YES"})
    logs = load_json(LOGS_FILE, [])
    
    return f'''
    <html>
    <head><title>Sniper Dashboard</title></head>
    <body style="background:#0e1117; color:white; font-family:sans-serif; padding:30px;">
        <div style="max-width:1000px; margin:auto;">
            <h1 style="color:#00f2ff; border-bottom: 2px solid #00f2ff; padding-bottom:10px;">🚀 Sniper Bot Dashboard</h1>
            
            <div style="display:flex; gap:25px; margin:30px 0;">
                <div style="background:#1a1c24; padding:25px; border-radius:15px; flex:1; border-left: 5px solid {'#00ff00' if state['status']=='ON' else '#ff4b4b'};">
                    <h3>Status do Bot: <span style="color:{'#00ff00' if state['status']=='ON' else '#ff4b4b'}">{state['status']}</span></h3>
                    <form action="/toggle" method="post" style="margin-top:15px;">
                        <button name="action" value="ON" style="background:#00ff00; color:black; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold; margin-right:10px;">LIGAR</button>
                        <button name="action" value="OFF" style="background:#ff4b4b; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">DESLIGAR</button>
                    </form>
                </div>
                
                <div style="background:#1a1c24; padding:25px; border-radius:15px; flex:1; text-align:center;">
                    <h3>Relatórios</h3>
                    <p>Exporte o histórico completo das operações.</p>
                    <a href="/download_pdf" style="background:#007bff; color:white; padding:12px 25px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block; margin-top:10px;">📥 BAIXAR PDF</a>
                </div>
            </div>

            <h2 style="margin-top:40px;">📜 Histórico de Operações</h2>
            <table style="width:100%; border-collapse:collapse; background:#1a1c24; border-radius:10px; overflow:hidden;">
                <tr style="background:#262730; text-align:left;">
                    <th style="padding:15px;">Data/Hora</th>
                    <th style="padding:15px;">Mercado</th>
                    <th style="padding:15px;">Lado</th>
                    <th style="padding:15px;">Status</th>
                </tr>
                {''.join([f"<tr style='border-bottom:1px solid #333;'><td style='padding:12px;'>{l.get('data','')}</td><td style='padding:12px;'>{l.get('mercado','')}</td><td style='padding:12px;'>{l.get('lado','')}</td><td style='padding:12px;'>{l.get('resultado','')}</td></tr>" for l in logs[:15]])}
            </table>
        </div>
    </body>
    </html>
    '''

@app.route('/toggle', methods=['POST'])
def toggle():
    if not session.get('logged_in'): return redirect(url_for('login'))
    action = request.form.get('action')
    save_json(BOT_STATE_FILE, {"status": action, "preference": "YES"})
    registrar_log(f"Bot alterado manualmente para {action}", "SISTEMA", "OK")
    return redirect(url_for('dashboard'))

@app.route('/download_pdf')
def download_pdf():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        pdf_bytes = gerar_pdf_bytes()
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"relatorio_sniper_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}", 500

if __name__ == "__main__":
    # Para execução local (no Render usa-se Gunicorn)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
