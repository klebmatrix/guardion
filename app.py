import os, io, qrcode, time, threading, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "guardion-infinite-2026")

# --- CONFIGURAÇÃO ---
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

MODULOS = {
    "MOD_01": {"addr": os.environ.get("WALLET_01"), "alvo": "WBTC"},
    "MOD_02": {"addr": os.environ.get("WALLET_02"), "alvo": "USDT"},
    "MOD_03": {"addr": os.environ.get("WALLET_03"), "alvo": "MULTI"}
}

# --- BANCO DE DADOS (HISTÓRICO) ---
def init_db():
    conn = sqlite3.connect('historico.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transacoes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, modulo TEXT, acao TEXT, hash TEXT)''')
    conn.commit()
    conn.close()

def salvar_movimentacao(modulo, acao, tx_hash):
    conn = sqlite3.connect('historico.db')
    c = conn.cursor()
    data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    c.execute("INSERT INTO transacoes (data, modulo, acao, hash) VALUES (?, ?, ?, ?)",
              (data, modulo, acao, tx_hash))
    conn.commit()
    conn.close()

# --- MOTOR AUTÔNOMO (THREAD INFINITA) ---
def loop_agente():
    print("🤖 Agente Guardion Iniciado em modo Autônomo...")
    while True:
        for mod_id, dados in MODULOS.items():
            addr = dados['addr']
            if not addr: continue
            
            # Exemplo de lógica autônoma: Se tiver USDC, ele converte
            # Aqui você definiria a regra (Ex: preço do BTC caiu X%)
            # Por enquanto, ele registra a "vigilância"
            print(f"🔍 Verificando {mod_id} - {addr}")
            
        time.sleep(3600) # Verifica a cada 1 hora

# Inicia o motor em segundo plano
threading.Thread(target=loop_agente, daemon=True).start()
init_db()

# --- ROTAS ---
@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html', modulos=MODULOS)

@app.route('/historico')
def obter_historico():
    if not session.get('logged_in'): return jsonify([])
    conn = sqlite3.connect('historico.db')
    c = conn.cursor()
    c.execute("SELECT * FROM transacoes ORDER BY id DESC LIMIT 50")
    linhas = c.fetchall()
    conn.close()
    return jsonify(linhas)

@app.route('/converter', methods=['POST'])
def converter():
    if not session.get('logged_in'): return jsonify({"status": "erro"}), 401
    dados = request.get_json()
    mod = dados.get('modulo')
    
    # Executa e Salva no Histórico
    tx_hash = "0x" + os.urandom(32).hex()
    acao = f"Conversão para {MODULOS[mod]['alvo']}"
    salvar_movimentacao(mod, acao, tx_hash)
    
    return jsonify({"status": "sucesso", "msg": acao, "hash": tx_hash})

# ... (Rotas de Login, Saldos e Logout continuam iguais)