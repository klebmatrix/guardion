import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. SETUP & DB ---
st.set_page_config(page_title="GUARDION OMNI v16.5", layout="wide")
db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# --- 2. CONEXÃO BLOCKCHAIN (ORÁCULO CHAINLINK) ---
# Usamos o RPC da Polygon para pegar o preço REAL do BTC sem usar APIs externas
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def pegar_preco_blockchain():
    try:
        # Endereço do Oráculo Chainlink BTC/USD na Polygon
        btc_proxy_addr = "0xc907E119666Ab23c568f4E9F06A3f2E10E4dd48E"
        abi = '[{"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}]'
        contract = w3.eth.contract(address=btc_proxy_addr, abi=abi)
        # O preço vem com 8 casas decimais
        return float(contract.functions.latestAnswer().call() / 10**8)
    except:
        return None

# --- 3. LOGICA DE EXECUÇÃO INFINITA ---
st.title("🛡️ GUARDION OMNI | CICLO INFINITO 2026")
btc = pegar_preco_blockchain()

if btc:
    st.metric("BTC ATUAL (VIA ORÁCULO)", f"${btc:,.2f}", delta="⛓️ BLOCKCHAIN DATA")
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        
        # COMPRA (QUEDA)
        if status == "VIGILANCIA" and btc <= alvo:
            try:
                if w3.eth.get_balance(addr) > 0:
                    acc = Account.from_key(priv)
                    tx = {'nonce': w3.eth.get_transaction_count(acc.address), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                    shs = w3.to_hex(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, priv).raw_transaction))
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit(); st.toast(f"🎯 {nome} COMPROU!")
            except: pass

        # VENDA (SUBIDA + RESET INFINITO)
        elif status == "COMPRADO" and btc >= (p_compra + 200):
            try:
                acc = Account.from_key(priv)
                tx = {'nonce': w3.eth.get_transaction_count(acc.address), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                shs = w3.to_hex(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, priv).raw_transaction))
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit(); st.toast(f"💰 {nome} LUCROU!")
            except: pass
    
    # Grid de visualização
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                if ag[5] == "COMPRADO": st.success(f"LUCRO: +${btc - ag[6]:.0f}")
                else: st.info(f"🎯 Target: ${ag[4]:,.0f}")
else:
    st.error("🚨 FALHA NA REDE POLYGON: Tentando reconectar...")
    time.sleep(10)
    st.rerun()

# Sidebar e Refresh
with st.sidebar:
    if st.button("🚀 REINICIAR SNIPERS"):
        db.execute("DELETE FROM agentes")
        p_base = btc if btc else 100000.0 
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_base - (i * 100), "VIGILANCIA", "---"))
        db.commit(); st.rerun()

time.sleep(30); st.rerun()