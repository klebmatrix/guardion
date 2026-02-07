import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. SETUP & DB ---
st.set_page_config(page_title="GUARDION OMNI v16.0 INFINITO", layout="wide")
db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()
agentes_raw = db.execute("SELECT * FROM agentes").fetchall()

# --- 2. LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🛡️ QG GUARDION - MODO INFINITO")
    if st.text_input("Chave:", type="password") == st.secrets.get("SECRET_KEY", "mestre2026"):
        if st.button("ATIVAR"): st.session_state.logado = True; st.rerun()
    st.stop()

# --- 3. CONEXÃO RPC ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def get_btc():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price'])
    except: return None

def assinar_tx(privada, para_endereco):
    try:
        acc = Account.from_key(privada)
        tx = {'nonce': w3.eth.get_transaction_count(acc.address), 'to': para_endereco, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
        signed = w3.eth.account.sign_transaction(tx, privada)
        return w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
    except: return "ERRO"

# --- 4. MOTOR INFINITO ---
st.title("♾️ SNIPER MODO INFINITO ATIVO")
btc = get_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    for ag in agentes_raw:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        
        # LOGICA DE COMPRA (QUEDA)
        if status == "VIGILANCIA" and btc <= alvo:
            if w3.eth.get_balance(addr) > 0:
                shs = assinar_tx(priv, addr)
                if "0x" in shs:
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit(); st.toast(f"🎯 {nome} COMPROU!")
        
        # LOGICA DE VENDA (LUCRO DE $200) - CICLO INFINITO
        elif status == "COMPRADO" and btc >= (p_compra + 200):
            shs = assinar_tx(priv, addr)
            if "0x" in shs:
                # Volta para VIGILANCIA para comprar de novo no mesmo alvo!
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit(); st.toast(f"💰 {nome} LUCROU E RESETOU!")

# --- 5. COMANDOS ---
with st.sidebar:
    pk_m = st.text_input("PK Mestre (22 POL):", type="password")
    if st.button("🚀 GERAR BATALHÃO"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            alvo_calc = btc - (i * 100)
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo_calc, "VIGILANCIA", "---"))
        db.commit(); st.rerun()
    
    if st.button("⛽ ABASTECER"):
        mestre = Account.from_key(pk_m)
        n = w3.eth.get_transaction_count(mestre.address, 'pending')
        for ag in db.execute("SELECT endereco FROM agentes LIMIT 10").fetchall():
            tx = {'nonce': n, 'to': ag[0], 'value': w3.to_wei(0.5, 'ether'), 'gas': 21000, 'gasPrice': int(w3.eth.gas_price*1.5), 'chainId': 137}
            w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, pk_m).raw_transaction)
            n += 1; time.sleep(4)
        st.success("Combustível enviado!")

# --- 6. GRID ---
t1, t2 = st.tabs(["🎯 GRID", "📄 LOGS"])
with t1:
    cols = st.columns(5)
    for idx, ag in enumerate(agentes_raw):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                if ag[5] == "COMPRADO": st.success(f"LUCRO: +${btc - ag[6]:.0f}")
                else: st.info(f"🎯 ${ag[4]:,.0f}")
with t2:
    import pandas as pd
    st.dataframe(pd.DataFrame(agentes_raw), width='stretch')

time.sleep(60); st.rerun()