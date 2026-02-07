import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. SETUP ---
st.set_page_config(page_title="GUARDION OMNI v16.1 INFINITO", layout="wide")

db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# Carregamento preventivo
agentes_raw = db.execute("SELECT * FROM agentes").fetchall()

# --- 2. LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🛡️ QG GUARDION - MODO INFINITO")
    senha_in = st.text_input("Chave:", type="password")
    if st.button("ATIVAR"):
        if senha_in == st.secrets.get("SECRET_KEY", "mestre2026"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 3. CONEXÃO RPC ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def get_btc():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        return float(r.json()['price'])
    except: return None

def enviar_tx_real(privada):
    try:
        acc = Account.from_key(privada)
        tx = {'nonce': w3.eth.get_transaction_count(acc.address), 'to': acc.address, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
        signed = w3.eth.account.sign_transaction(tx, privada)
        return w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
    except: return "ERRO"

# --- 4. MOTOR DE EXECUÇÃO INFINITA ---
st.title("♾️ CICLO INFINITO ATIVO")
btc = get_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    for ag in agentes_raw:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        
        # LÓGICA DE COMPRA (QUEDA)
        if status == "VIGILANCIA" and btc <= alvo:
            if w3.eth.get_balance(addr) > 0:
                shs = enviar_tx_real(priv)
                if shs.startswith("0x"):
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit(); st.toast(f"🎯 {nome} COMPROU!")

        # LÓGICA DE VENDA (LUCRO $200 + RESET INFINITO)
        elif status == "COMPRADO" and btc >= (p_compra + 200):
            shs = enviar_tx_real(priv)
            if shs.startswith("0x"):
                # O Pulo do Gato: Volta para VIGILANCIA com o mesmo alvo
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit(); st.toast(f"💰 {nome} LUCROU E RESETOU!")
else:
    st.warning("⚠️ API Binance ocupada. Aguardando conexão...")

# --- 5. COMANDOS ---
with st.sidebar:
    pk_m = st.text_input("PK Mestre (22 POL):", type="password")
    if st.button("🚀 LANÇAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        preco_base = btc if btc else 100000.0 # FIX PARA O ERRO TYPEERROR
        for i in range(50):
            acc = Account.create()
            alvo_calc = preco_base - (i * 100)
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo_calc, "VIGILANCIA", "---"))
        db.commit(); st.rerun()

    if st.button("⛽ ABASTECER"):
        if pk_m:
            mestre = Account.from_key(pk_m)
            n = w3.eth.get_transaction_count(mestre.address, 'pending')
            for ag in db.execute("SELECT endereco FROM agentes LIMIT 10").fetchall():
                tx = {'nonce': n, 'to': ag[0], 'value': w3.to_wei(0.5, 'ether'), 'gas': 21000, 'gasPrice': int(w3.eth.gas_price*1.5), 'chainId': 137}
                w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, pk_m).raw_transaction)
                n += 1; time.sleep(4)
            st.success("Abastecimento em curso!")

# --- 6. GRID ---
t1, t2 = st.tabs(["🎯 MONITOR", "📄 LOGS"])
with t1:
    if agentes_raw:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes_raw):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    if ag[5] == "COMPRADO": st.success(f"PROCESSO: +${btc - ag[6]:.0f}")
                    else: st.info(f"🎯 ${ag[4]:,.0f}")

with t2:
    if agentes_raw:
        import pandas as pd
        df = pd.DataFrame(agentes_raw, columns=['ID','Nome','Endereço','Privada','Alvo','Status','Preço','Hash'])
        st.dataframe(df[['Nome', 'Status', 'Alvo', 'Hash']], width='stretch')

time.sleep(60); st.rerun()