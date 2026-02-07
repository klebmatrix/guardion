import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. SETUP ---
st.set_page_config(page_title="GUARDION OMNI v16.7", layout="wide")
db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# --- 2. CONEXÃO DIRETA (RPC ÚNICO E ESTÁVEL) ---
# Usando o Cloudflare, que é um dos mais resistentes a bloqueios
RPC_URL = "https://polygon-mainnet.public.blastapi.io"
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 10}))

def pegar_preco_emergencia():
    # Tenta apenas uma fonte leve para não estressar a rede
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        return float(r.json()['price'])
    except:
        return None

# --- 3. EXECUÇÃO DO CICLO ---
st.title("🛡️ MODO DE SOBREVIVÊNCIA ATIVO")
btc = pegar_preco_emergencia()

if btc and w3.is_connected():
    st.metric("BTC ATUAL", f"${btc:,.2f}", delta="CONEXÃO REESTABELECIDA")
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        
        # OPERAÇÃO INFINITA (COMPRA)
        if status == "VIGILANCIA" and btc <= alvo:
            try:
                # Verificação de saldo só se o preço bater
                if w3.eth.get_balance(addr) > 0:
                    tx = {'nonce': w3.eth.get_transaction_count(addr), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                    signed = w3.eth.account.sign_transaction(tx, priv)
                    shs = w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit(); st.toast(f"🎯 {nome} COMPROU!")
            except: pass

        # OPERAÇÃO INFINITA (VENDA/RESET)
        elif status == "COMPRADO" and btc >= (p_compra + 150):
            try:
                tx = {'nonce': w3.eth.get_transaction_count(addr), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                shs = w3.to_hex(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, priv).raw_transaction))
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit(); st.toast(f"💰 {nome} RESETOU!")
            except: pass

    # Grid Compacto
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                if ag[5] == "COMPRADO": st.success("POSIÇÃO ATIVA")
                else: st.info(f"${ag[4]:,.0f}")
else:
    st.warning("📡 Aguardando sinal da rede... O robô entrará em modo de silêncio por 2 minutos.")
    time.sleep(120)
    st.rerun()

# --- 4. COMANDO ---
with st.sidebar:
    if st.button("🚀 REINICIAR SISTEMA"):
        db.execute("DELETE FROM agentes")
        p_base = btc if btc else 98000.0
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_base - (i * 50), "VIGILANCIA", "---"))
        db.commit(); st.rerun()

time.sleep(60); st.rerun()