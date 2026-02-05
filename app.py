import os, datetime, requests, time
from flask import Flask, request, redirect, url_for, session
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO CORE ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA") 
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# ENDEREÇOS OFICIAIS POLYGON
USDC_ADDR = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
WETH_ADDR = Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619")
QUICK_ROUTER_ADDR = Web3.to_checksum_address("0xa5E0829CaCEd8fFDD03942104b10503958965ee4")

# ABI MÍNIMA PARA SWAP (QuickSwap/Uniswap V2)
ROUTER_ABI = [
    {"name":"swapExactETHForTokens","type":"function","inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"payable"}
]

def get_balances():
    try:
        pol = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
        return f"{pol:.4f}"
    except:
        return "0.0000"

@app.route('/executar_tudo', methods=['POST'])
def executar_tudo():
    if not session.get('auth') or not PVT_KEY: return "ERRO: ACESSO NEGADO"
    acao = request.form.get('acao')
    
    try:
        nonce = w3.eth.get_transaction_count(WALLET)
        gas_price = w3.eth.gas_price
        
        if acao == "swap_pol_usdc":
            # Troca 0.1 POL por USDC como teste de segurança
            router = w3.eth.contract(address=QUICK_ROUTER_ADDR, abi=ROUTER_ABI)
            path = [Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"), USDC_ADDR] # MATIC -> USDC
            
            tx = router.functions.swapExactETHForTokens(
                0, # amountOutMin (0 para teste, em prod usar slippage)
                path,
                WALLET,
                int(time.time()) + 600
            ).build_transaction({
                'from': WALLET,
                'value': w3.to_wei(0.1, 'ether'),
                'gas': 250000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': 137
            })
            
            signed = w3.eth.account.sign_transaction(tx, PVT_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            return redirect(f"/?msg=SWAP_ENVIADO_{w3.to_hex(tx_hash)[:8]}")

        if acao == "transferir":
            tx = {
                'nonce': nonce, 'to': Web3.to_checksum_address(request.form.get('para')),
                'value': w3.to_wei(request.form.get('valor'), 'ether'),
                'gas': 21000, 'gasPrice': gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PVT_KEY)
            w3.eth.send_raw_transaction(signed.rawTransaction)
            return redirect("/?msg=TRANSFERENCIA_SUCESSO")

    except Exception as e:
        return f"ERRO NA OPERAÇÃO: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<body style="background:#000;color:orange;text-align:center;padding-top:100px;"><h1>COMMAND CENTER</h1><form method="post"><input type="password" name="pin" autofocus><button>LOGAR</button></form></body>'

@app.route('/')
def dash():
    if not session.get('auth'): return redirect('/login')
    saldo = get_balances()
    msg = request.args.get('msg', '')
    
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:850px; margin:auto; border:2px solid orange; padding:20px; background:#000;">
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid orange; padding-bottom:10px;">
                <h2 style="color:orange; margin:0;">⚡ SNIPER MASTER v43</h2>
                <div>SALDO: <b style="color:cyan;">{saldo} POL</b></div>
            </div>

            <p style="color:lime; font-size:12px;">{msg}</p>

            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:20px; margin-top:20px;">
                
                <div style="background:#111; padding:15px; border:1px solid #333;">
                    <h3 style="color:orange; margin:0;">🔄 SWAP INSTANTÂNEO</h3>
                    <p style="font-size:11px; color:#666;">Trocar POL por USDC via QuickSwap</p>
                    <form action="/executar_tudo" method="post">
                        <input type="hidden" name="acao" value="swap_pol_usdc">
                        <button style="width:100%; padding:10px; background:orange; color:black; font-weight:bold; cursor:pointer;">EXECUTAR SWAP (0.1 POL)</button>
                    </form>
                </div>

                <div style="background:#111; padding:15px; border:1px solid #333;">
                    <h3 style="color:cyan; margin:0;">💸 TRANSFERIR</h3>
                    <form action="/executar_tudo" method="post">
                        <input type="hidden" name="acao" value="transferir">
                        <input name="para" placeholder="Destino 0x..." style="width:100%; margin:5px 0;">
                        <input name="valor" placeholder="Qtde POL" style="width:100%; margin:5px 0;">
                        <button style="width:100%; padding:10px; background:cyan; color:black; font-weight:bold; cursor:pointer;">ENVIAR POL</button>
                    </form>
                </div>

                <div style="background:#111; padding:15px; border:1px solid #333;">
                    <h3 style="color:magenta; margin:0;">🎯 SNIPER TARGET</h3>
                    <p>ALVO: 14.4459</p>
                    <div style="color:lime; font-size:12px;">VIGIANDO REDE...</div>
                    <button style="width:100%; margin-top:10px; background:#222; color:#fff; border:1px solid #444;">EDITAR ALVO</button>
                </div>

            </div>
            
            <div style="margin-top:20px; padding:10px; background:#0a0a0a; border:1px solid #222; font-size:11px; color:#444;">
                CONECTADO: {WALLET}<br>
                SEGURANÇA: Transações assinadas localmente no Render.
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 15000);</script>
    </body>"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)