import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. CONFIGURAÇÃO DE PÁGINA (DEVE SER A PRIMEIRA COISA) ---
st.set_page_config(page_title="COMMANDER OMNI", layout="wide")

# --- 2. SISTEMA DE LOGIN ---
def login():
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if not st.session_state.logado:
        st.title("🔐 QG GUARDION | LOGIN")
        try:
            senha_mestre = st.secrets["SECRET_KEY"]
        except:
            senha_mestre = "mestre123" # Senha padrão se o Secret falhar
        
        senha_input = st.text_input("Senha de Acesso:", type="password")
        if st.button("ENTRAR"):
            if senha_input == senha_mestre:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        st.stop()

login()

# --- 3. INICIALIZAÇÃO DO BANCO (PROTEGIDA) ---
def init_db():
    conn = sqlite3.connect('guardion_v4.db', check_same_thread=False)
    # Garante que a tabela existe antes de qualquer SELECT
    conn.execute('''CREATE TABLE IF NOT EXISTS agentes_v4 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- 4. INTERFACE E LÓGICA ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.title("🛡️ PAINEL OPERACIONAL")

with st.sidebar:
    st.header("⚙️ COMANDO")
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()
    
    st.divider()
    pk_m = st.text_input("Sua PK_01:", type="password")
    
    if st.button("🚀 GERAR 25 SNIPERS"):
        db.execute("DELETE FROM agentes_v4")
        novos = []
        for i in range(25):
            acc = Account.create()
            alvo = 102500.0 - (i * 200)
            novos.append((f"SNIPER-{i+1:02d}", acc.address, acc.key.hex(), alvo, "VIGILANCIA", 0.0, "Aguardando"))
        db.executemany("INSERT INTO agentes_v4 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)", novos)
        db.commit()
        st.success("Batalhão Criado!")
        st.rerun()

# --- 5. EXIBIÇÃO DOS AGENTES (AGORA SEGURO) ---
try:
    btc = float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price'])
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    
    # Busca os agentes - Se a tabela estiver vazia, ele apenas não mostra nada (sem erro)
    agentes = db.execute("SELECT * FROM agentes_v4").fetchall()
    
    if agentes:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    st.caption(f"Status: {ag[5]}")
                    st.write(f"🎯 ${ag[4]:,.0f}")
    else:
        st.info("Nenhum sniper em campo. Use o botão 'Gerar' na lateral.")

except Exception as e:
    st.error("Erro de conexão ou banco de dados. Tente dar 'Reboot' no app.")

time.sleep(30)
st.rerun()