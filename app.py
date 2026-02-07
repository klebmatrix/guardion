import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. SETUP & DB ---
st.set_page_config(page_title="GUARDION OMNI v16.3", layout="wide")
db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# --- 2. MOTOR DE PREÇO COM TOLERÂNCIA A FALHAS ---
def pegar_preco_btc():
    # Tenta Binance
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        return float(r.json()['price'])
    except:
        # Tenta CoinGecko (Backup)
        try:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
            return float(r.json()['bitcoin']['usd'])
        except:
            return None

# --- 3. CONEXÃO RPC ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def assinar_tx(privada, para_addr):
    try:
        acc = Account.from_key(privada)
        tx = {
            'nonce': w3.eth.get_transaction_count(acc.address),
            'to': para_addr,
            'value': 0,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 137
        }
        signed = w3.eth.account.sign_transaction(tx, privada)
        return w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
    except: return "ERRO"

# --- 4. LÓGICA DE EXECUÇÃO ---
st.title("♾️ COMANDO SNIPER INFINITO")
btc = pegar_preco_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}", delta="CONEXÃO OK")
    agentes_raw = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes_raw:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        
        # COMPRA (QUEDA)
        if status == "VIGILANCIA" and btc <= alvo:
            if w3.eth.get_balance(addr) > 0:
                shs = assinar_tx(priv, addr)
                if shs.startswith("0x"):
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit()
        
        # VENDA & REINÍCIO (LUCRO $150)
        elif status == "COMPRADO" and btc >= (p_compra + 150):
            shs = assinar_tx(priv, addr)
            if shs.startswith("0x"):
                # RESET PARA VIGILÂNCIA (MODO INFINITO)
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit()
else:
    st.warning("🔄 Link instável. O sistema tentará novamente em 60s para evitar bloqueio.")
    time.sleep(60)
    st.rerun()

# --- 5. INTERFACE ---
with st.sidebar:
    st.subheader("Configurações")
    if st.button("🚀 GERAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        p_base = btc if btc else 100000.0
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_base - (i * 100), "VIGILANCIA", "---"))
        db.commit()
        st.rerun()

# GRID DE STATUS
if btc:
    agentes_view = db.execute("SELECT * FROM agentes").fetchall()
    cols = st.columns(5)
    for idx, ag in enumerate(agentes_view):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                if ag[5] == "COMPRADO":
                    lucro_atual = btc - ag[6]
                    st.success(f"PROCESSO: +${lucro_atual:.0f}")
                else:
                    st.info(f"🎯 Target: ${ag[4]:,.0f}")

# Refresh longo para evitar novos banimentos de IP
time.sleep(60)
st.rerun()