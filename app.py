import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="COMMANDER OMNI v11.9", layout="wide")

# --- 2. LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    senha_mestre = st.secrets.get("SECRET_KEY", "mestre2026")
    st.title("🔐 ACESSO AO QG")
    senha_input = st.text_input("Senha:", type="password")
    if st.button("ENTRAR"):
        if senha_input == senha_mestre:
            st.session_state.logado = True
            st.rerun()
        else: st.error("Senha Incorreta")
    st.stop()

# --- 3. BANCO DE DADOS ---
db = sqlite3.connect('guardion_v5.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v5 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
db.commit()

# --- 4. MOTOR DE PREÇO RESILIENTE (TENTA 3 FONTES) ---
def buscar_preco_btc_total():
    # Fonte 1: Binance
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3)
        return float(r.json()['price'])
    except: pass
    
    # Fonte 2: Kraken
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDT", timeout=3)
        return float(r.json()['result']['XBTUSDT']['c'][0])
    except: pass
    
    # Fonte 3: Coinbase
    try:
        r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=3)
        return float(r.json()['data']['amount'])
    except: pass
    
    return None

# --- 5. INTERFACE ---
st.title("🛡️ COMMANDER OMNI | v11.9")

btc = buscar_preco_btc_total()

if btc:
    st.metric("BTC ATUAL (Média Global)", f"${btc:,.2f}")
    
    with st.sidebar:
        st.header("⚙️ COMANDO")
        if st.button("🚀 REGERAR 25 SNIPERS"):
            db.execute("DELETE FROM agentes_v5")
            novos = []
            for i in range(25):
                acc = Account.create()
                alvo = 102500.0 - (i * 200)
                novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo, "VIGILANCIA", 0.0, "Start"))
            db.executemany("INSERT INTO agentes_v5 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)", novos)
            db.commit()
            st.rerun()
        
        if st.button("🚪 LOGOUT"):
            st.session_state.logado = False
            st.rerun()

    # Mostrar Agentes
    agentes = db.execute("SELECT * FROM agentes_v5").fetchall()
    if agentes:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    st.caption(f"🎯 ${ag[4]:,.0f}")
                    if ag[5] == "COMPRADO": st.success("POSICIONADO")
                    else: st.info("VIGILÂNCIA")
    else:
        st.warning("Sem agentes. Clique em 'Regerar' na lateral.")
else:
    st.error("🚨 ERRO DE REDE: Todos os servidores de preço (Binance, Kraken, Coinbase) falharam.")
    st.info("Isso pode ser um problema temporário no servidor do Streamlit. Tentando novamente...")
    time.sleep(10)
    st.rerun()

time.sleep(30)
st.rerun()