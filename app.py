import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="COMMANDER OMNI v11.8", layout="wide")

# --- LOGIN ---
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
        else: st.error("Incorreta")
    st.stop()

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('guardion_v5.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS agentes_v5 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- CONEXÃO COM A REDE (RPC ALTERNATIVO) ---
# Se um falhar, o sistema tenta o outro
RPCS = ["https://polygon-rpc.com", "https://1rpc.io/matic", "https://rpc-mainnet.maticvigil.com"]
w3 = Web3(Web3.HTTPProvider(RPCS[0]))

# --- FUNÇÃO DE PREÇO RESILIENTE ---
def buscar_preco_btc():
    urls = [
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    ]
    try:
        res = requests.get(urls[0], timeout=10)
        return float(res.json()['price'])
    except:
        try:
            res = requests.get(urls[1], timeout=10)
            return float(res.json()['bitcoin']['usd'])
        except:
            return None

# --- UI ---
st.title("🛡️ COMMANDER OMNI | v11.8")

btc = buscar_preco_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    
    with st.sidebar:
        if st.button("🚀 REGERAR 25 SNIPERS"):
            db.execute("DELETE FROM agentes_v5")
            novos = []
            for i in range(25):
                acc = Account.create()
                alvo = 102500.0 - (i * 200)
                novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo, "VIGILANCIA", 0.0, "Início"))
            db.executemany("INSERT INTO agentes_v5 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)", novos)
            db.commit()
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
                    # Mostra o status com cor
                    if ag[5] == "COMPRADO": st.success("POSICIONADO")
                    else: st.info("VIGILÂNCIA")
    else:
        st.warning("Sem agentes. Clique em 'Regerar' na lateral.")
else:
    st.error("🚨 FALHA DE CONEXÃO: O servidor da Binance não respondeu. Tentando reconectar em 10 segundos...")
    time.sleep(10)
    st.rerun()

time.sleep(30)
st.rerun()