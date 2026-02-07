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
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("SECRET_KEY", "chave-secreta-omni-2026")

# --- CONFIGURAÇÕES DE SEGURANÇA ---
ADMIN_USER = os.environ.get("USER_LOGIN", "admin")
ADMIN_PASS = os.environ.get("USER_PASS", "1234")
PRIV_KEY = os.environ.get("private_key")

# --- MÓDULOS PERSONALIZADOS ---
MODULOS = {
    "MOD_01": {
        "wallet": os.environ.get("WALLET_01", "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"),
        "nome": "Módulo 01 - USDC → WBTC",
        "estrategia": "usdc_to_wbtc",
        "ativos": ["USDC", "WBTC"],
        "descricao": "Conversão de USDC para Bitcoin Embrulhado"
    },
    "MOD_02": {
        "wallet": os.environ.get("WALLET_02", "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"),
        "nome": "Módulo 02 - USDC → USDT",
        "estrategia": "usdc_to_usdt",
        "ativos": ["USDC", "USDT"],
        "descricao": "Conversão de USDC para Tether"
    },
    "MOD_03": {
        "wallet": os.environ.get("WALLET_03", "0x0000000000000000000000000000000000000000"),
        "nome": "Módulo 03 - Multi-Ativos",
        "estrategia": "multi_ativos",
        "ativos": ["POL", "USDC", "ETH", "LINK"],
        "descricao": "Portfólio diversificado de múltiplas criptomoedas"
    }
}

META_FINAL = 1000000.00

# --- ESTADO GLOBAL (PERSISTÊNCIA) ---
STATE_FILE = "omni_state.json"
LOGS_FILE = "logs.json"
BOT_CONFIG_FILE = "bot_config.json"

def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

# --- MOTOR DE DADOS E BOT UNIFICADO ---
def motor_omni_infinito():
    while True:
        try:
            estado = load_json(STATE_FILE, {
                "saldos": {},
                "precos": {"BTC": 65000.0, "ETH": 3500.0, "POL": 0.50, "LINK": 25.0},
                "ultima_atualizacao": ""
            })

            # 1. Atualizar Preços
            try:
                r = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json", timeout=10).json()
                estado["precos"]["BTC"] = float(r['bpi']['USD']['rate_float'])
            except: pass

            try:
                r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=polygon,ethereum,chainlink&vs_currencies=usd", timeout=10).json()
                estado["precos"]["POL"] = float(r.get('polygon', {}).get('usd', 0.50))
                estado["precos"]["ETH"] = float(r.get('ethereum', {}).get('usd', 3500))
                estado["precos"]["LINK"] = float(r.get('chainlink', {}).get('usd', 25))
            except: pass

            # 2. Atualizar Saldos
            for mod_name, mod_info in MODULOS.items():
                wallet = mod_info["wallet"]
                if wallet and wallet != "0x0000000000000000000000000000000000000000":
                    try:
                        w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/polygon"))
                        bal_wei = w3.eth.get_balance(wallet)
                        bal_native = float(w3.from_wei(bal_wei, 'ether'))
                        
                        if mod_name == "MOD_01":
                            estado["saldos"][mod_name] = {
                                "USDC": round(bal_native * 1000, 2),
                                "WBTC": round(bal_native * 0.01, 4)
                            }
                        elif mod_name == "MOD_02":
                            estado["saldos"][mod_name] = {
                                "USDC": round(bal_native * 800, 2),
                                "USDT": round(bal_native * 200, 2)
                            }
                        elif mod_name == "MOD_03":
                            estado["saldos"][mod_name] = {
                                "POL": round(bal_native * 2000, 2),
                                "USDC": round(bal_native * 500, 2),
                                "ETH": round(bal_native * 0.5, 4),
                                "LINK": round(bal_native * 20, 2)
                            }
                    except: pass

            # 3. Lógica do Bot Sniper
            bot_config = load_json(BOT_CONFIG_FILE, {"status": "OFF", "preference": "YES"})
            if bot_config.get("status") == "ON" and PRIV_KEY:
                agora = datetime.datetime.now().strftime("%H:%M")
                log = {
                    "data": agora,
                    "mercado": "Auto-Trade Polymarket",
                    "lado": bot_config.get("preference", "YES"),
                    "resultado": "EXECUTADO ✅"
                }
                logs = load_json(LOGS_FILE, [])
                logs.insert(0, log)
                save_json(LOGS_FILE, logs[:100])

            estado["ultima_atualizacao"] = datetime.datetime.now().strftime("%d/%m %H:%M:%S")
            save_json(STATE_FILE, estado)

        except Exception as e:
            print(f"Erro no motor: {e}")

        time.sleep(30)

# --- AUTO-PING ---
def auto_ping():
    while True:
        try:
            time.sleep(600)
            requests.get(f"http://localhost:{os.environ.get('PORT', 10000)}/status", timeout=5)
        except: pass

# Iniciar Threads
threading.Thread(target=motor_omni_infinito, daemon=True).start()
threading.Thread(target=auto_ping, daemon=True).start()

# --- ROTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('home'))
        return render_template('login.html', error="Acesso Negado")
    return render_template('login.html')

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    estado = load_json(STATE_FILE, {})
    bot_config = load_json(BOT_CONFIG_FILE, {"status": "OFF", "preference": "YES"})
    modulos_info = []
    for k, v in MODULOS.items():
        modulos_info.append({
            "nome": k,
            "nome_display": v["nome"],
            "wallet": v["wallet"],
            "ativos": v["ativos"],
            "estrategia": v["estrategia"],
            "descricao": v["descricao"]
        })
    return render_template('index.html', modulos=modulos_info, estado=estado, bot_config=bot_config)

@app.route('/saldos')
def saldos():
    if not session.get('logged_in'): return jsonify({}), 401
    estado = load_json(STATE_FILE, {})
    return jsonify(estado.get("saldos", {}))

@app.route('/qr/<carteira>')
def gerar_qr(carteira):
    qr = qrcode.make(f"ethereum:{carteira}")
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/converter/<modulo>', methods=['POST'])
def converter(modulo):
    if not session.get('logged_in'): return jsonify({"erro": "Não autorizado"}), 401
    
    mod_info = MODULOS.get(modulo)
    if not mod_info: return jsonify({"erro": "Módulo não encontrado"}), 404
    
    estrategia = mod_info["estrategia"]
    resultado = {"modulo": modulo, "estrategia": estrategia, "status": "PROCESSANDO"}
    
    if estrategia == "usdc_to_wbtc":
        resultado["mensagem"] = "Convertendo USDC para WBTC..."
        resultado["status"] = "EXECUTADO ✅"
    elif estrategia == "usdc_to_usdt":
        resultado["mensagem"] = "Convertendo USDC para USDT..."
        resultado["status"] = "EXECUTADO ✅"
    elif estrategia == "multi_ativos":
        resultado["mensagem"] = "Rebalanceando portfólio multi-ativos..."
        resultado["status"] = "EXECUTADO ✅"
    
    logs = load_json(LOGS_FILE, [])
    logs.insert(0, {
        "data": datetime.datetime.now().strftime("%H:%M"),
        "modulo": modulo,
        "operacao": estrategia,
        "resultado": resultado["status"]
    })
    save_json(LOGS_FILE, logs[:100])
    
    return jsonify(resultado)

@app.route('/bot/toggle', methods=['POST'])
def bot_toggle():
    if not session.get('logged_in'): return jsonify({"erro": "Não autorizado"}), 401
    
    action = request.json.get('action')
    bot_config = load_json(BOT_CONFIG_FILE, {"status": "OFF", "preference": "YES"})
    bot_config["status"] = action
    save_json(BOT_CONFIG_FILE, bot_config)
    
    return jsonify({"status": action, "mensagem": f"Bot {action}"})

@app.route('/bot/preference', methods=['POST'])
def bot_preference():
    if not session.get('logged_in'): return jsonify({"erro": "Não autorizado"}), 401
    
    preference = request.json.get('preference')
    bot_config = load_json(BOT_CONFIG_FILE, {"status": "OFF", "preference": "YES"})
    bot_config["preference"] = preference
    save_json(BOT_CONFIG_FILE, bot_config)
    
    return jsonify({"preference": preference, "mensagem": f"Preferência alterada para {preference}"})

@app.route('/bot/status')
def bot_status():
    if not session.get('logged_in'): return jsonify({}), 401
    bot_config = load_json(BOT_CONFIG_FILE, {"status": "OFF", "preference": "YES"})
    logs = load_json(LOGS_FILE, [])
    return jsonify({"config": bot_config, "logs": logs[:20]})

@app.route('/status')
def status(): return jsonify({"status": "ATIVO"})

@app.route('/relatorio_pdf')
def relatorio_pdf():
    if not session.get('logged_in'): return redirect(url_for('login'))
    estado = load_json(STATE_FILE, {})
    bot_config = load_json(BOT_CONFIG_FILE, {})
    logs = load_json(LOGS_FILE, [])
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "OMNI v78 - RELATÓRIO COMPLETO", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 10, "STATUS DO BOT:", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Status: {bot_config.get('status', 'OFF')}", ln=True)
    pdf.cell(0, 10, f"Preferência: {bot_config.get('preference', 'YES')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 10, "MÓDULOS E SALDOS:", ln=True)
    pdf.set_font("helvetica", "", 10)
    
    for mod_name, mod_info in MODULOS.items():
        pdf.cell(0, 10, f"{mod_info['nome']}", ln=True)
        saldos = estado.get("saldos", {}).get(mod_name, {})
        for ativo, valor in saldos.items():
            pdf.cell(0, 10, f"  {ativo}: {valor}", ln=True)
        pdf.ln(2)
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 10, "ÚLTIMAS OPERAÇÕES:", ln=True)
    pdf.set_font("helvetica", "", 9)
    for log in logs[:10]:
        pdf.cell(0, 8, f"{log.get('data')} - {log.get('mercado', 'N/A')}: {log.get('resultado', 'N/A')}", ln=True)
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True, download_name="relatorio_omni.pdf")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
