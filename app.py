import os, datetime, time, threading, requests
from flask import Flask, session, redirect
from web3 import Web3

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURAÇÃO MASTER ---
PIN = os.environ.get("guardiao")
WALLET = Web3.to_checksum_address("0xD885C5f2bbE54D3a7D4B2a401467120137F0CCbE")
PVT_KEY = os.environ.get("CHAVE_PRIVADA")
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Histórico para o bot decidir a tendência
historico_precos = []
logs = []

def add_log(msg):
    logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 20: logs.pop()

def motor_decisao_ia():
    add_log("🧠 CÉREBRO ALGORÍTMICO INICIADO")
    while True:
        try:
            # 1. PEGAR PREÇO REAL (Simulado - Substitua pela sua API de mercado)
            preco_atual = 14.21 # O preço que você me passou
            historico_precos.append(preco_atual)
            if len(historico_precos) > 10: historico_precos.pop(0)

            # 2. CALCULAR TENDÊNCIA (Média Simples)
            if len(historico_precos) > 5:
                media = sum(historico_precos) / len(historico_precos)
                tendencia = "ALTA" if preco_atual > media else "BAIXA"
                
                # O BOT DECIDE AQUI:
                bal_wei = w3.eth.get_balance(WALLET)
                pol_real = float(w3.from_wei(bal_wei, 'ether'))

                # DECISÃO DE COMPRA: Preço baixo + Tendência de virada
                if pol_real > 1.0 and tendencia == "ALTA" and preco_atual < 14.45:
                    add_log(f"🤖 DECISÃO: Oportunidade detectada em {preco_atual}. COMPRANDO...")
                    # executar_swap_pol_usdc()
                
                # DECISÃO DE VENDA: Proteção ou Lucro
                elif pol_real < 1.0: # Assume que está em USDC
                    if preco_atual > 14.70:
                        add_log(f"🤖 DECISÃO: Lucro máximo atingido ({preco_atual}). VENDENDO!")
                        # executar_swap_usdc_pol()
                    elif preco_atual < 14.00:
                        add_log(f"🤖 DECISÃO: Risco de quebra. Saindo do mercado em {preco_atual}.")
                        # executar_swap_usdc_pol()
                
                add_log(f"📊 Análise: Preço {preco_atual} | Tendência: {tendencia}")
            else:
                add_log("⏳ Coletando dados para decidir melhor...")

        except Exception as e:
            add_log(f"❌ Falha: {str(e)[:25]}")
        
        time.sleep(15) # O bot analisa o mercado a cada 15 segundos

threading.Thread(target=motor_decisao_ia, daemon=True).start()

@app.route('/')
def dashboard():
    if not session.get('auth'): return redirect('/login')
    log_render = "".join([f"<div style='border-bottom:1px solid #222;padding:5px;'>{l}</div>" for l in logs])
    return f"""
    <body style="background:#050505; color:#eee; font-family:monospace; padding:20px;">
        <div style="max-width:800px; margin:auto; border:2px solid lime; padding:20px; background:#000;">
            <h2 style="color:lime;">🤖 BOT AUTÔNOMO v46</h2>
            <div style="background:#111; padding:10px; margin-bottom:20px;">
                <b>MODO:</b> TOTALMENTE AUTOMATIZADO (DECISÃO PRÓPRIA)<br>
                <b>SALDO POL:</b> {w3.from_wei(w3.eth.get_balance(WALLET), 'ether'):.4f}
            </div>
            <div style="background:#0a0a0a; height:350px; overflow-y:auto; padding:10px; font-size:12px; color:#0f0;">
                {log_render}
            </div>
        </div>
        <script>setTimeout(()=>location.reload(), 10000);</script>
    </body>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pin') == PIN:
        session['auth'] = True
        return redirect('/')
    return '<h1>LOGIN ALGORITMO</h1><form method="post"><input type="password" name="pin" autofocus><button>ENTRAR</button></form>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)