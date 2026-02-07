import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="COMMANDER OMNI INFINITO", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def init_db():
    conn = sqlite3.connect('guardion_v4.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS agentes_v4 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- AUTOMAÇÃO DE FUNDO ---
def loop_de_combate(pk_mestre, btc_preço, lucro_alvo):
    agentes = db.execute("SELECT * FROM agentes_v4").fetchall()
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, acao = ag
        
        # 1. VERIFICAR COMPRA
        if status == "VIGILANCIA" and btc_preço <= alvo and btc_preço > 0:
            db.execute("UPDATE agentes_v4 SET status='COMPRADO', preco_compra=?, ultima_acao='COMPRA EXECUTADA' WHERE id=?", (btc_preço, id_b))
            db.commit()
            
        # 2. VERIFICAR VENDA (LUCRO)
        elif status == "COMPRADO" and btc_preço >= (p_compra + lucro_alvo):
            db.execute("UPDATE agentes_v4 SET status='VIGILANCIA', preco_compra=0, ultima_acao='LUCRO NO BOLSO' WHERE id=?", (id_b,))
            db.commit()

        # 3. AUTO-ABASTECER (Se tiver PK Mestre na sessão)
        if pk_mestre:
            try:
                if w3.eth.get_balance(addr) < w3.to_wei(0.1, 'ether'):
                    acc_m = Account.from_key(pk_mestre)
                    tx = {'nonce': w3.eth.get_transaction_count(acc_m.address), 'to': addr, 'value': w3.to_wei(0.5, 'ether'), 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                    signed = w3.eth.account.sign_transaction(tx, pk_mestre)
                    w3.eth.send_raw_transaction(signed.raw_transaction)
            except: pass

# --- UI ---
st.title("🛡️ COMMANDER OMNI | MODO INFINITO")

with st.sidebar:
    pk_m = st.text_input("PK_01 (Mestre):", type="password")
    lucro = st.number_input("Lucro Alvo ($):", value=500.0)
    if st.button("🚀 LANÇAR 25 SNIPERS"):
        # ... (lógica de geração igual à anterior)
        pass

# Execução automática ao carregar a página
btc_agora = float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price'])
loop_de_combate(pk_m if pk_m else None, btc_agora, lucro)

# Mostra o status atual
st.success(f"O sistema está vigilante. Preço BTC: ${btc_agora:,.2f}")
# ... resto do código de exibição das colunas ...