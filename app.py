import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v12.2", layout="wide")

# --- LOGIN SEGURO ---
# Define a senha mestra vinda do secrets ou padrão
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")

if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.2")
    senha_input = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha_input == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
        else: st.error("Chave Incorreta")
    st.stop()

# --- BANCO DE DADOS ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
db.commit()

# --- MOTOR DE PREÇO ---
def pegar_preco():
    try: 
        return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()['price'])
    except: return None

# --- ENGINE DE OPERAÇÃO ATIVA INFINITA ---
def rodar_engine(btc_atual, tp_porcentagem):
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    for ag in agentes:
        id_ag, nome, _, _, alvo, status, preco_compra, _ = ag
        
        # COMPRA AUTOMÁTICA
        if btc_atual <= alvo and status == "VIGILANCIA":
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultima_acao=? WHERE id=?", 
                       (btc_atual, f"Compra em ${btc_atual:,.2f}", id_ag))
            db.commit()
            st.toast(f"🎯 {nome} COMPROU!")

        # TAKE PROFIT INFINITO (VENDA)
        elif status == "COMPRADO":
            meta = preco_compra * (1 + (tp_porcentagem / 100))
            if btc_atual >= meta:
                # Volta para VIGILANCIA para reentrada infinita
                db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, ultima_acao=? WHERE id=?", 
                           (f"Lucro em ${btc_atual:,.2f} | Reiniciado", id_ag))
                db.commit()
                st.toast(f"💰 {nome} LUCROU E REINICIOU!")

# --- DASHBOARD ---
st.title("🛡️ COMMANDER OMNI v12.2")
btc = pegar_preco()

if btc:
    st.metric("BTC/USDT", f"${btc:,.2f}")

    with st.sidebar:
        st.header("⚙️ CONFIGURAÇÕES")
        # PK agora fica na sessão para não sumir no refresh
        if "pk_gas" not in st.session_state: st.session_state.pk_gas = ""
        st.session_state.pk_gas = st.text_input("Sua PK (Gás):", value=st.session_state.pk_gas, type="password")
        
        tp = st.slider("Take Profit (%)", 0.1, 5.0, 1.5)
        dist = st.number_input("Espaçamento Grid ($)", value=100)

        if st.button("🚀 LANÇAR BATALHÃO"):
            db.execute("DELETE FROM agentes_v6")
            for i in range(50):
                acc = Account.create()
                db.execute("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)",
                           (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), btc - (i * dist), "VIGILANCIA", 0.0, "Pronto"))
            db.commit()
            st.success("50 Agentes em campo!")
            st.rerun()

    # Executa a lógica de trade
    rodar_engine(btc, tp)

    # Visualização
    tab1, tab2 = st.tabs(["Monitor", "Dados"])
    with tab1:
        ags = db.execute("SELECT * FROM agentes_v6").fetchall()
        cols = st.columns(5)
        for i, a in enumerate(ags):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.caption(f"Status: {a[5]}")
                    if a[5] == "COMPRADO": st.success(f"Dono de BTC")

    with tab2:
        df = pd.DataFrame(ags, columns=['ID', 'Nome', 'End', 'Key', 'Alvo', 'Status', 'P.Compra', 'Ação'])
        st.dataframe(df[['Nome', 'Status', 'Alvo', 'Ação']])

else:
    st.warning("⚠️ Aguardando sinal da rede...")

time.sleep(15)
st.rerun()