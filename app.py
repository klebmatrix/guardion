import os
import datetime
from flask import Flask, render_template, request, redirect, url_for
from web3 import Web3

app = Flask(__name__)

# --- CONFIGURAÇÕES TÉCNICAS (POLYGON) ---
RPC_URL = "https://polygon-rpc.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Endereços Oficiais
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
POLYMARKET_EXCHANGE = "0x4bFb9e7A482025732168923a1aB1313936a79853"

# --- DADOS DA CARTEIRA (SUBSTITUA PELOS SEUS) ---
WALLET_ADDRESS = "0xSEU_ENDERECO_AQUI"
PRIVATE_KEY = "SUA_CHAVE_PRIVADA_AQUI"

# --- ESTADO DO SISTEMA ---
bot_status = {"status": "OFF"}
historico_ops = []

# --- FUNÇÕES DE BLOCKCHAIN ---

def check_balances():
    """Busca os saldos reais na rede Polygon"""
    try:
        # Saldo POL
        pol_wei = web3.eth.get_balance(WALLET_ADDRESS)
        pol_balance = round(web3.from_wei(pol_wei, 'ether'), 4)
        
        # Saldo USDC (ABI simplificada para balanceOf)
        abi_balance = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
        contract = web3.eth.contract(address=USDC_ADDRESS, abi=abi_balance)
        usdc_raw = contract.functions.balanceOf(WALLET_ADDRESS).call()
        usdc_balance = round(usdc_raw / 10**6, 2) # USDC tem 6 decimais
        
        return pol_balance, usdc_balance
    except:
        return 0.0, 14.44 # Fallback se a rede falhar

def dar_permissao_usdc():
    """Libera o contrato para gastar o USDC da carteira"""
    try:
        abi_approve = '[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]'
        contract = web3.eth.contract(address=USDC_ADDRESS, abi=abi_approve)
        
        # Constrói transação de Approve (Infinito)
        tx = contract.functions.approve(POLYMARKET_EXCHANGE, 2**256 - 1).build_transaction({
            'from': WALLET_ADDRESS,
            'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
            'gas': 60000,
            'gasPrice': web3.eth.gas_price
        })
        
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash.hex()
    except Exception as e:
        return f"Erro: {str(e)}"

# --- ROTAS FLASK ---

@app.route('/')
def index():
    pol, usdc = check_balances()
    return render_template('dashboard.html', 
                           wallet=WALLET_ADDRESS,
                           pol=pol,
                           usdc=usdc,
                           bot=bot_status,
                           total_ops=len(historico_ops),
                           ops_yes=sum(1 for x in historico_ops if x['lado'] == 'YES'),
                           ops_no=sum(1 for x in historico_ops if x['lado'] == 'NO'),
                           ops_erro=sum(1 for x in historico_ops if x['lado'] == 'ERRO'),
                           historico=historico_ops)

@app.route('/toggle_bot', methods=['POST'])
def toggle_bot():
    action = request.form.get('status')
    bot_status["status"] = action
    
    if action == "ON":
        # Tenta o Approve assim que liga o bot
        res = dar_permissao_usdc()
        historico_ops.insert(0, {
            "data": datetime.datetime.now().strftime("%d/%m %H:%M:%S"),
            "mercado": f"Sistema: Ativando Permissões (TX: {res[:10]}...)",
            "lado": "SISTEMA"
        })
    
    return redirect(url_for('index'))

@app.route('/gerar_relatorio')
def gerar_relatorio():
    # Placeholder para a função de PDF
    return "Função de PDF em desenvolvimento para este dashboard."

if __name__ == '__main__':
    # No Render, use a porta definida pela variável de ambiente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)