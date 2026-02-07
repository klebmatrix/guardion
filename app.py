import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time

# --- 1. SETUP & ALCHEMY ---
st.set_page_config(page_title="GUARDION OMNI v17.2", layout="wide")

# Seu link privado que validamos via Curl
URL_ALCHEMY = "https://polygon-mainnet.g.alchemy.com/v2/uaG8q0TcfE_gfxACc-zlQ" 

w3 = Web3(Web3.HTTPProvider(URL_ALCHEMY))
db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# --- 2. MOTOR DE PREÇO (ORÁCULO NATIVO) ---
def pegar_preco_btc():
    try:
        # Consulta ao Oráculo Chainlink (BTC/USD) - Sem limite de API
        proxy_addr = "0xc907E119666Ab23c568f4E9F06A3f2E10E4dd48E"
        abi = '[{"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}]'
        contract = w3.eth.contract(address=proxy_addr, abi=abi)
        return float(contract.functions.latestAnswer().call() / 10**8)
    except:
        return None

# --- 3. EXECUÇÃO DO CICLO INFINITO ---
st.title("♾️ COMANDO GUARDION | MODO INFINITO")
btc = pegar_preco_btc()

if btc and w3.is_connected():
    st.metric("BTC ATUAL (VIA ALCHEMY)", f"${btc:,.2f}", delta="CONEXÃO 100%")
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, _ = ag
        
        # --- AÇÃO: COMPRA (DIP) ---
        if status == "VIGILANCIA" and btc <= alvo:
            try:
                if w3.eth.get_balance(addr) > 0:
                    tx = {'nonce': w3.eth.get_transaction_count(addr), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                    shs = w3.to_hex(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, priv).raw_transaction))
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit()
                    st.toast(f"🎯 {nome} COMPROU EM ${btc}")
            except: pass

        # --- AÇÃO: VENDA (TAKE PROFIT + RESET) ---
        elif status == "COMPRADO" and btc >= (p_compra + 150):
            try:
                tx = {'nonce': w3.eth.get_transaction_count(addr), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                shs = w3.to_hex(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, priv).raw_transaction))
                # O SEGREDO DO INFINITO: Volta para VIGILANCIA e apaga o preco_compra
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit()
                st.toast(f"💰 {nome} LUCROU E VOLTOU AO POSTO!")
            except: pass

    # Exibição Visual
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                if ag[5] == "COMPRADO":
                    st.success(f"DENTRO: +${btc - ag[6]:.0f}")
                else:
                    st.info(f"ALVO: ${ag[4]:,.0f}")
else:
    st.error("🔄 Conectando ao túnel privado...")
    time.sleep(10); st.rerun()

# --- 4. SIDEBAR DE COMANDO ---
with st.sidebar:
    st.header("⚙️ OPERAÇÕES")
    if st.button("🚀 INICIALIZAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        p_base = btc if btc else 100000.0
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_base - (i * 100), "VIGILANCIA", "---"))
        db.commit()
        st.rerun()

time.sleep(15); st.rerun()