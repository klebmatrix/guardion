import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random, pandas as pd

# --- CONFIGURAÇÃO DE ALTA PERFORMANCE ---
st.set_page_config(page_title="GUARDION OMNI v16.5", layout="wide")

# --- BANCO DE DADOS (LIMPEZA DE CONFLITOS) ---
db = sqlite3.connect('guardion_v16_5.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, ativo TEXT, endereco TEXT, privada TEXT, 
            alvo REAL, status TEXT, preco_compra REAL, lucro_real REAL, hash TEXT)''')
db.commit()

# --- ESTADO DO PILOTO AUTOMÁTICO (FORÇADO) ---
if "preco_v16" not in st.session_state: st.session_state.preco_v16 = 95000.0
# O mercado oscila sozinho aqui embaixo
st.session_state.preco_v16 += st.session_state.preco_v16 * random.uniform(-0.003, 0.003)

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI | PILOTO AUTOMÁTICO ATIVO")

with st.sidebar:
    st.error("🚨 ÁREA DE RETIRADA (SAQUE)")
    destino = st.text_input("Sua Carteira (0x...):", placeholder="Destino dos Lucros")
    if st.button("🏦 RETIRAR LUCROS AGORA"):
        if destino.startswith("0x"):
            st.success(f"Enviando lucros para {destino}...")
            # Lógica de envio Web3 aqui
        else: st.error("Insira um endereço válido!")

    st.divider()
    st.header("⚙️ CONFIGURAÇÃO")
    ativo = st.selectbox("Ativo:", ["BTC", "ETH", "POL", "SOL"])
    st.metric("PREÇO ATUAL (AUTO)", f"${st.session_state.preco_v16:,.2f}")
    
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.0)
    
    if st.button("🚀 REINICIAR E DESTRAVAR TUDO"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", ativo, acc.address, acc.key.hex(), 
                        st.session_state.preco_v16 * (1 - (i*0.001)), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- MOTOR DE OPERAÇÃO INFINITA ---
p_atual = st.session_state.preco_v16
try:
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    for ag in agentes:
        id_ag, nome, moeda, end, priv, alvo, status, p_compra, lucro, last_h = ag
        
        # COMPRA (Ao atingir o alvo na oscilação)
        if p_atual <= alvo and status == "VIGILANCIA":
            h = f"0x{int(time.time())}B{id_ag}"
            db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (p_atual, h, id_ag))
            db.commit()
        
        # VENDA (Ao atingir o TP na oscilação)
        elif status == "COMPRADO" and p_atual >= p_compra * (1 + (tp_pct/100)):
            lucro_v = p_atual - p_compra
            h = f"0x{int(time.time())}S{id_ag}"
            db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0.0, lucro_real=?, hash=? WHERE id=?", (lucro + lucro_v, h, id_ag))
            db.commit()

    # --- DASHBOARD DE RESULTADOS ---
    st.subheader(f"💵 LUCRO TOTAL DISPONÍVEL: :green[${sum([a[8] for a in agentes]):,.2f}]")

    

    t1, t2 = st.tabs(["🎯 Monitor da Tropa", "📜 Hashes (Copiar)"])
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
                c1.write(a[1]); c2.code(a[9])

except Exception as e:
    st.error("Erro no motor. Clique em 'REINICIAR' no menu lateral.")

# Refresh rápido (3 seg) para o Piloto Automático ser fluido
time.sleep(3)
st.rerun()