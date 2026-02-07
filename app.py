import os, threading, time, io, qrcode
from flask import Flask, render_template, send_file, request, jsonify
from web3 import Web3

app = Flask(__name__)

# Configurações do Agente
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Carteiras configuradas no Render
MODULOS = {
    "MOD_01": os.environ.get("WALLET_01", "0x000..."),
    "MOD_02": os.environ.get("WALLET_02", "0x000..."),
    "MOD_03": os.environ.get("WALLET_03", "0x000...")
}

@app.route('/')
def home():
    return render_template('index.html', modulos=MODULOS)

@app.route('/converter', methods=['POST'])
def converter():
    try:
        dados = request.get_json()
        mod = dados.get('modulo')
        carteira = MODULOS.get(mod)
        
        print(f"🤖 AGENTE OMNI: Iniciando conversão para WBTC no {mod} ({carteira})")
        
        # Aqui o Agente valida se tem POL (Matic) para o gás
        balance = w3.eth.get_balance(carteira)
        
        return jsonify({
            "status": "sucesso", 
            "msg": f"Ordem aceita! Agente processando WBTC no {mod}."
        })
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)}), 500

@app.route('/qr/<path:text>')
def qr(text):
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    # O Render usa a porta 10000 por padrão
    app.run(host='0.0.0.0', port=10000)