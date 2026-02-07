import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONFIGURAÇÃO DE ALTA VELOCIDADE ---
st.set_page_config(page_title="GUARDION v17.1 - CONTROL", layout="wide")

# --- MEMÓRIA DO SISTEMA ---
if "p" not in st.session_state: st.session_state.p = 98500.0
if "pilot_active" not in st.session_state: st.session_state.pilot_active = True

# --- CONEXÃO E DB ---
db = sqlite3.connect('guardion_v17_1.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, p_compra REAL, lucro REAL, last_tx TEXT)''')
db.commit()

# --- INTERFACE DE COMANDO ---
st.title("⚡ GUARDION v17.1 | TRAVA DE COMANDO ATIVA")

with st.sidebar:
    st.header("🎮 PAINEL DE IGNIÇÃO")
    
    # Trava do Piloto Automático com persistência
    st.session_state.pilot_active = st.toggle("🚀 LIGAR PILOTO AUTOMÁTICO", value=st.session_state.pilot_active)
    
    if st.session_state.pilot_active:
        st.success("MOTOR: RODANDO (SIN ATIVO)")
        # Oscilação do preço só acontece se a trava estiver ligada
        st.session_state.p += st.session_state.p * random.uniform(-0.008, 0.008)
    else:
        st.error("MOTOR: TRAVADO (SINAL ESTÁTICO)")

    st.divider()
    st.subheader("💰 RETIRADA REAL")
    carteira_saque = st.text_input("Sua Carteira (0x...):", key="dest_real")
    
    if st.button("🔥 RESET & ACORDAR SNIPERS"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- MOTOR DE EXECUÇÃO ---
p_atual = st.session_state.p
agentes = db.execute("SELECT * FROM agentes").fetchall()

for ag in agentes:
    id_a, nome, end, priv, status, p_c, lucro, tx = ag
    
    # Lógica de Compra (Só age se o piloto estiver ligado)
    if st.session_state.pilot_active:
        if p_atual <= 98500.0 and status == "VIGILANCIA":
            db.execute("UPDATE agentes SET status='COMPRADO', p_compra=? WHERE id=?", (p_atual, id_a))
        
        # Lógica de Venda (Take Profit)
        elif status == "COMPRADO" and p_atual >= p_c * 1.005:
            db.execute("UPDATE agentes SET status='VIGILANCIA', p_compra=0.0, lucro=? WHERE id=?", 
                       (lucro + (p_atual - p_c), id_a))
db.commit()

# --- DASHBOARD ---
st.metric("PREÇO ATUAL", f"${p_atual:,.2f}", delta=f"{'ATIVO' if st.session_state.pilot_active else 'PAUSADO'}")



st.subheader(f"💵 LUCRO TOTAL REALIZADO: :green[${sum([a[6] for a in agentes]):,.2f}]")

cols = st.columns(5)
for i, a in enumerate(agentes):
    with cols[i % 5]:
        with st.container(border=True):
            st.write(f"**{a[1]}**")
            st.write(f"Lucro: ${a[6]:,.2f}")
            st.caption(f"{a[4]}")

# Refresh condicional (Mais lento se travado, rápido se rodando)
time.sleep(1 if st.session_state.pilot_active else 3)
st.rerun()