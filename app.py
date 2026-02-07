import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. SETUP ---
st.set_page_config(page_title="GUARDION OMNI v14.3 REAL", layout="wide")

# --- 2. BANCO DE DADOS ---
db = sqlite3.connect('guardion_real_v14.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

agentes = db.execute("SELECT * FROM agentes").fetchall()

# --- 3. LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    senha_mestre = st.secrets.get("SECRET_KEY", "mestre2026")
    st.title("🔐 ACESSO AO QG REAL")
    senha_digitada = st.text_input("Senha de Comando:", type="password")
    if st.button("ENTRAR"):
        if senha_digitada == senha_mestre:
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 4. CONEXÃO RPC & FUNÇÕES BLOCKCHAIN ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def pegar_preco_btc():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        return float(r.json()['price'])
    except: return None

def executar_compra_na_rede(privada_agente):
    try:
        acc = Account.from_key(privada_agente)
        saldo = w3.eth.get_balance(acc.address)
        if saldo < w3.to_wei(0.001, 'ether'): return "ERRO: SEM POL (GAS)"
        
        tx = {'nonce': w3.eth.get_transaction_count(acc.address), 'to': acc.address, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
        signed = w3.eth.account.sign_transaction(tx, privada_agente)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return w3.to_hex(tx_hash)
    except Exception as e: return f"FALHA: {str(e)[:10]}"

def abastecer_agentes(pk_mestre):
    try:
        mestre = Account.from_key(pk_mestre)
        agentes_alvo = db.execute("SELECT endereco FROM agentes LIMIT 10").fetchall()
        for ag in agentes_alvo:
            tx = {'nonce': w3.eth.get_transaction_count(mestre.address), 'to': ag[0], 'value': w3.to_wei(0.5, 'ether'), 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
            signed = w3.eth.account.sign_transaction(tx, pk_mestre)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            time.sleep(1.5)
        return True
    except: return False

# --- 5. INTERFACE ---
st.title("🛡️ COMMANDER OMNI | v14.3")
btc = pegar_preco_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        if status == "VIGILANCIA" and btc <= alvo:
            shs = executar_compra_na_rede(priv)
            if shs.startswith("0x"):
                db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                db.commit()
                st.toast(f"✅ {nome} disparou na rede!")

# --- 6. SIDEBAR ---
with st.sidebar:
    pk_m = st.text_input("PK_01 (Mestre):", type="password")
    if st.button("🚀 LANÇAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            alvo_calc = btc - (i * 100) if btc else 100000 - (i * 100)
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo_calc, "VIGILANCIA", "---"))
        db.commit()
        st.rerun()
    if st.button("⛽ ABASTECER (0.5 POL)"):
        if abastecer_agentes(pk_m): st.success("Abastecidos!")
        else: st.error("Falha no envio")

# --- 7. VISUALIZAÇÃO (CORRIGIDA PARA 2026) ---
tab1, tab2 = st.tabs(["🎯 GRID", "📄 LOGS (SHS/HASH)"])
with tab1:
    if agentes:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    if "0x" in str(ag[7]): st.success("EXECUTADO")
                    else: st.info(f"🎯 ${ag[4]:,.0f}")
with tab2:
    if agentes:
        import pandas as pd
        df = pd.DataFrame(agentes, columns=['ID','Nome','Carteira','Privada','Alvo','Status','Preço','Hash'])
        df['Ver no Scan'] = df['Hash'].apply(lambda x: f"https://polygonscan.com/tx/{x}" if x.startswith('0x') else x)
        # CORREÇÃO AQUI: width='stretch' substitui use_container_width=True
        st.dataframe(df[['Nome', 'Status', 'Ver no Scan', 'Carteira']], width='stretch')

time.sleep(20); st.rerun()