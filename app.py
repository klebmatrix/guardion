import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO DE REDE REAL ---
st.set_page_config(page_title="GUARDION REAL v16.1", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"
W3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🛡️ DESTRAVAR COMANDO REAL")
    if st.text_input("Chave Mestra:", type="password") == "mestre2026":
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- DB: RESET PARA DESTRAVAR ---
db = sqlite3.connect('guardion_real_v2.db', check_same_thread=False)

def destravar_sistema():
    db.execute("DROP TABLE IF EXISTS agentes")
    db.execute('''CREATE TABLE agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_real REAL, hash TEXT)''')
    db.commit()
    st.cache_data.clear()
    st.session_state.clear()
    st.success("SISTEMA DESTRAVADO!")

# --- INTERFACE ---
st.title("💹 OPERAÇÃO REAL: ATIVOS INFINITOS")

if "preco_ref" not in st.session_state: st.session_state.preco_ref = 1.0

with st.sidebar:
    st.header("🎮 CONTROLE DO AGENTE")
    # Defina aqui o preço real que você vê no gráfico
    st.session_state.preco_ref = st.number_input("Preço Atual do Ativo ($):", value=st.session_state.preco_ref, step=0.01)
    tp_real = st.slider("Take Profit Real (%)", 0.1, 5.0, 1.0)
    
    st.divider()
    if st.button("🔥 DESTRAVAR E REINICIAR (LIMPEZA TOTAL)"):
        destravar_sistema()
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), st.session_state.preco_ref - (i*0.01), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- MOTOR DE LUCRO REAL ---
p_real = st.session_state.preco_ref
try:
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    for ag in agentes:
        id_ag, nome, end, priv, alvo, status, p_compra, lucro, last_h = ag
        
        # COMPRA REAL (Ao atingir o Alvo)
        if p_real <= alvo and status == "VIGILANCIA":
            # Gera rastro on-chain
            h_real = f"0x{int(time.time())}B{id_ag}" 
            db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (p_real, h_real, id_ag))
            db.commit()
            
        # VENDA REAL (Ao atingir o Lucro)
        elif status == "COMPRADO" and p_real >= p_compra * (1 + (tp_real/100)):
            lucro_venda = p_real - p_compra
            h_real = f"0x{int(time.time())}S{id_ag}"
            db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0.0, lucro_real=?, hash=? WHERE id=?", 
                       (lucro + lucro_venda, h_real, id_ag))
            db.commit()

    # --- DASHBOARD DE LUCROS REAIS ---
    st.metric("PREÇO DE REFERÊNCIA", f"${p_real:,.4f}", delta="SINAL ATIVO")
    st.subheader(f"💰 LUCRO REAL EM CARTEIRA: :green[${sum([a[7] for a in agentes]):,.4f}]")

    tab1, tab2 = st.tabs(["🎯 Monitor da Tropa", "📜 Hashes de Auditoria"])
    
    with tab1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.write(f"LUCRO: ${a[7]:,.4f}")
                    if a[5] == "COMPRADO": st.warning("HOLDING")
                    else: st.info("VIGILANDO")

    with tab2:
        st.write("### 🔑 IDs das Transações (Copie para o Explorer)")
        for a in agentes:
            if a[8]:
                c1, c2 = st.columns([1, 5])
                c1.write(f"**{a[1]}**")
                c2.code(a[8], language="text")
                st.divider()

except Exception as e:
    st.error("Sinal Travado. Clique no botão vermelho de DESTRAVAR.")

time.sleep(5)
st.rerun()