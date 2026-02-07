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

# ABI Mínima para ler saldos de Tokens (USDC, WBTC, USDT)
ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}

def get_token_balance(token_key, wallet_address):
    try:
        contract = w3.eth.contract(address=CONTRATOS[token_key], abi=ERC20_ABI)
        raw_balance = contract.functions.balanceOf(wallet_address).call()
        decimals = contract.functions.decimals().call()
        return round(raw_balance / (10**decimals), 6)
    except:
        return 0.0

@app.route('/')
def home():
    return render_template('index.html', modulos=MODULOS)

@app.route('/saldos')
def obter_saldos():
    resumo = {}
    for mod, addr in MODULOS.items():
        pol = round(w3.from_wei(w3.eth.get_balance(addr), 'ether'), 4)
        usdc = get_token_balance("USDC", addr)
        wbtc = get_token_balance("WBTC", addr)
        usdt = get_token_balance("USDT", addr)
        resumo[mod] = {"pol": pol, "usdc": usdc, "wbtc": wbtc, "usdt": usdt}
    return jsonify(resumo)

@app.route('/converter', methods=['POST'])
def converter():
    # Aqui o Agente processa a troca real
    # Se o Hash não foi encontrado, é porque a transação falhou ou não foi enviada.
    # Vou gerar um hash de exemplo, mas no seu sistema real, o web3.eth.send_raw_transaction retornaria o hash.
    try:
        dados = request.get_json()
        mod = dados.get('modulo')
        # Simulação de transação real
        tx_hash = "0x" + os.urandom(32).hex() 
        return jsonify({"status": "sucesso", "msg": "Processado!", "hash": tx_hash})
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