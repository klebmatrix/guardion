import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="COMMANDER OMNI v11.7", layout="wide")

# --- 2. LOGIN (SENHA FIXA PARA NÃO TER ERRO DE SECRET) ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 ACESSO AO QG")
    # Tenta ler do Secret, se não achar, a senha é 'mestre2026'
    senha_mestre = st.secrets.get("SECRET_KEY", "mestre2026")
    
    senha_input = st.text_input("Senha de Acesso:", type="password")
    if st.button("ENTRAR"):
        if senha_input == senha_mestre:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("❌ Senha Incorreta!")
    st.stop()

# --- 3. BANCO DE DADOS COM AUTO-REPAIR ---
def init_db():
    try:
        conn = sqlite3.connect('guardion_v5.db', check_same_thread=False)
        conn.execute('''CREATE TABLE IF NOT EXISTS agentes_v5 
                        (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                        alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"Erro no Banco: {e}")
        return None

db = init_db()

# --- 4. INTERFACE E COMANDOS ---
st.title("🛡️ COMMANDER OMNI | OPERACIONAL")

with st.sidebar:
    st.header("⚙️ COMANDO")
    if st.button("SAIR / LOCK"):
        st.session_state.logado = False
        st.rerun()
    
    st.divider()
    pk_m = st.text_input("PK_01 (Mestre):", type="password")
    
    if st.button("🚀 LANÇAR 25 SNIPERS"):
        if db:
            db.execute("DELETE FROM agentes_v5")
            novos = []
            for i in range(25):
                acc = Account.create()
                alvo = 102500.0 - (i * 200)
                novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo, "VIGILANCIA", 0.0, "Aguardando"))
            db.executemany("INSERT INTO agentes_v5 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)", novos)
            db.commit()
            st.success("Batalhão v5 Criado!")
            st.rerun()

# --- 5. MONITORAMENTO ---
if db:
    try:
        # Preço BTC
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        btc = float(res.json()['price'])
        st.metric("BTC ATUAL", f"${btc:,.2f}")
        
        # Lista Agentes
        agentes = db.execute("SELECT * FROM agentes_v5").fetchall()
        if agentes:
            cols = st.columns(5)
            for idx, ag in enumerate(agentes):
                with cols[idx % 5]:
                    with st.container(border=True):
                        st.write(f"**{ag[1]}**")
                        st.caption(f"Status: {ag[5]}")
                        st.write(f"🎯 ${ag[4]:,.0f}")
        else:
            st.info("Aguardando criação dos agentes v5...")
            
    except Exception as e:
        st.warning("Aguardando conexão com a rede...")

# Loop de refresh
time.sleep(30)
st.rerun()