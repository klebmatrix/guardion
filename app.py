import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- SISTEMA DE LOGIN SEGURO ---
def login():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.title("🛡️ COMMANDER OMNI | ACESSO RESTRITO")
        
        # Tenta ler a senha dos Secrets, se não existir usa uma padrão
        try:
            senha_mestre = st.secrets["SECRET_KEY"]
        except:
            st.warning("⚠️ SECRET_KEY não configurada nos Secrets. Usando padrão: mestre123")
            senha_mestre = "mestre123"

        senha_input = st.text_input("Introduza a Chave do QG:", type="password")
        
        if st.button("AUTENTICAR"):
            if senha_input == senha_mestre:
                st.session_state.logado = True
                st.success("Acesso concedido!")
                st.rerun()
            else:
                st.error("Chave incorreta. Acesso negado.")
        st.stop() # Interrompe o código aqui se não estiver logado

login()

# --- SEÇÃO OPERACIONAL (SÓ CARREGA APÓS LOGIN) ---
st.set_page_config(page_title="COMMANDER OMNI", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

with st.sidebar:
    st.header("👤 COMANDANTE")
    if st.button("LOGOUT / SAIR"):
        st.session_state.logado = False
        st.rerun()
    st.divider()
    # Aqui entra o campo da PK_01 que já configuramos
    pk_m = st.text_input("PK_01 (Mestre):", type="password")

# --- BANCO E LÓGICA ---
conn = sqlite3.connect('guardion_v4.db', check_same_thread=False)
st.title("🛡️ PAINEL DE CONTROLO ATIVO")

# Exemplo de monitor de preço que já tínhamos
try:
    btc = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price']
    st.metric("BTC/USDT", f"${float(btc):,.2f}")
except:
    st.write("A aguardar conexão com a Binance...")

# Listagem dos 25 Agentes
agentes = conn.execute("SELECT * FROM agentes_v4").fetchall()
if agentes:
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                st.caption(f"Status: {ag[5]}")
else:
    st.info("Batalhão pronto para ser gerado.")

time.sleep(30)
st.rerun()