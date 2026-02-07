import os, threading, time, io, qrcode
from flask import Flask, render_template, send_file, request, jsonify
from web3 import Web3

app = Flask(__name__)

# Configuração da Rede Polygon
RPC_URL = os.environ.get("RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

MODULOS = {
    "MOD_01": os.environ.get("WALLET_01", "0x..."),
    "MOD_02": os.environ.get("WALLET_02", "0x..."),
    "MOD_03": os.environ.get("WALLET_03", "0x...")
}

@app.route('/')
def home():
    return render_template('index.html', modulos=MODULOS)

@app.route('/saldos')
def obter_saldos():
    resumo = {}
    for mod, addr in MODULOS.items():
        try:
            # Obtém saldo de POL (Matic) para o Gás
            balance_wei = w3.eth.get_balance(addr)
            balance_pol = round(w3.from_wei(balance_wei, 'ether'), 4)
            resumo[mod] = f"{balance_pol} POL"
        except:
            resumo[mod] = "Erro"
    return jsonify(resumo)

@app.route('/converter', methods=['POST'])
def converter():
    try:
        dados = request.get_json()
        mod = dados.get('modulo')
        hash_tx = "0x" + os.urandom(32).hex() # Simula envio da TX
        
        mensagens = {
            "MOD_01": "Conversão USDC ➔ WBTC",
            "MOD_02": "Conversão USDC ➔ USDT",
            "MOD_03": "Diversificação Ativa"
        }
        
        return jsonify({
            "status": "sucesso", 
            "msg": mensagens.get(mod, "Operação"),
            "hash": hash_tx
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
    app.run(host='0.0.0.0', port=10000)