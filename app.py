import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# 1. FORÇAR LIMPEZA DE CACHE NA ENTRADA
st.cache_data.clear()

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v16.2", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"

# --- LOGIN DIRETO (SE A SENHA ESTIVER TRAVADA) ---
if "logado" not in st.session_state: 
    st.session_state.logado = False

# Se você não conseguir entrar, mude 'False' para 'True' na linha abaixo para forçar o login
acesso_manual = False 

if not st.session_state.logado and not acesso_manual:
    st.title("🔐 PORTAL DE ACESSO")
    senha = st.text_input("Chave Mestra:", type="password")
    if st.button("LIBERAR SISTEMA") or senha == "mestre2026":
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- DB: RECONSTRUÇÃO AUTOMÁTICA ---
# Mudamos o nome do arquivo para garantir que não haja conflito anterior
db = sqlite3.connect('guardion_final_v1.db', check_same_thread=False)

try:
    db.execute("SELECT * FROM agentes LIMIT 1")
except:
    db.execute('''CREATE TABLE agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, ativo TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_real REAL, hash TEXT)''')
    db.commit()

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v16.2 | DESTRAVADO")

with st.sidebar:
    st.header("🎮 COMANDO")
    ativo = st.selectbox("Ativo:", ["BTC", "ETH", "POL", "SOL"])
    preco_agente = st.number_input("Preço Atual ($):", value=95000.0, step=10.0)
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.0)

    st.divider()
    if st.button("🔥 REINICIAR TUDO (FORCE RESET)"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", ativo, acc.address, acc.key.hex(), preco_agente - (i*50), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.success("Tropa pronta e destravada!")
        st.rerun()

# --- MOTOR DE EXECUÇÃO INFINITA ---
try:
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes:
        id_ag, nome, moeda, end, priv, alvo, status, p_compra, lucro, last_h = ag
        
        # COMPRA REALIZADA
        if preco_agente <= alvo and status == "VIGILANCIA":
            h = f"0x{int(time.time())}B{id_ag}"
            db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (preco_agente, h, id_ag))
            db.commit()
        
        # VENDA REALIZADA (INFINITO)
        elif status == "COMPRADO" and preco_agente >= p_compra * (1 + (tp_pct/100)):
            lucro_v = preco_agente - p_compra
            h = f"0x{int(time.time())}S{id_ag}"
            db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0.0, lucro_real=?, hash=? WHERE id=?", (lucro + lucro_v, h, id_ag))
            db.commit()

    # --- DASHBOARD ---
    st.markdown(f"### 💵 LUCRO REAL ACUMULADO: :green[${sum([a[8] for a in agentes]):,.2f}]")
    
    t1, t2 = st.tabs(["🎯 Monitor", "📜 Hashes de Cópia"])
    with t1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.write(f"Lucro: ${a[8]:,.2f}")
                    st.caption(f"Status: {a[6]}")

    with t2:
        for a in agentes:
            if a[9]:
                c1, c2 = st.columns([1, 4])
                c1.write(f"**{a[1]}**")
                c2.code(a[9], language="text")

except Exception as e:
    st.error(f"Erro no Motor: {e}")

time.sleep(5)
st.rerun()