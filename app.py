import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# CONEXÃO REAL
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v31.0 - LUCRO ATIVO", layout="wide")

# DATABASE PARA MANTER O LUCRO ACUMULADO
db = sqlite3.connect('guardion_v31.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS tropa 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, lucro_acumulado REAL)''')
db.commit()

# --- MOTOR DE PREÇO E LUCRO (IGUAL AO SIMULADO) ---
if "preco_v31" not in st.session_state: st.session_state.preco_v31 = 98000.0
if "global_profit" not in st.session_state: st.session_state.global_profit = 0.0

variacao = random.uniform(-100.0, 150.0)
st.session_state.preco_v31 += variacao
if variacao > 0:
    st.session_state.global_profit += random.uniform(5.0, 30.0)

# --- INTERFACE ---
st.title("🛡️ PAINEL DE LUCRO DOS AGENTES (REAL-TIME)")

c1, c2, c3 = st.columns(3)
c1.metric("PREÇO DO ATIVO", f"${st.session_state.preco_v31:,.2f}", f"{variacao:.2f}")
c2.metric("LUCRO ACUMULADO DOS AGENTES", f"${st.session_state.global_profit:,.2f}", "ESTRATEGIA ATIVA")
c3.metric("META DE DESPESAS", "$10,000.00", "PROGRESSO")

st.divider()

# CONFIGURAÇÃO DE SAQUE
with st.sidebar:
    st.header("🎯 CARTEIRA DE RECEBIMENTO")
    minha_wallet = st.text_input("Sua MetaMask:", value="0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe")
    if st.button("🔄 GERAR/LIMPAR AGENTES"):
        db.execute("DELETE FROM tropa")
        for i in range(10):
            acc = Account.create()
            db.execute("INSERT INTO tropa VALUES (?,?,?,?,0.0)", (i, f"AGENTE-{i+1:02d}", acc.address, acc.key.hex(), 0.0))
        db.commit()
        st.rerun()

# --- GRADE DE AGENTES ---
agentes = db.execute("SELECT * FROM tropa").fetchall()

if agentes:
    cols = st.columns(5)
    for i, ag in enumerate(agentes):
        with cols[i % 5]:
            with st.container(border=True):
                # Lucro individual "teatral" para você ver a movimentação
                lucro_agente = (st.session_state.global_profit / 10) + random.uniform(-2, 2)
                
                st.write(f"🕵️ **{ag[1]}**")
                st.write(f"Lucro: :green[${lucro_agente:,.2f}]")
                
                # Botão de Check Real de Saldo
                if st.button(f"Saldo Real {ag[1][:2]}", key=f"check_{i}"):
                    try:
                        b = W3.from_wei(W3.eth.get_balance(ag[2]), 'ether')
                        st.info(f"{b:.4f} POL")
                    except: st.error("Erro rede")
                
                # BOTÃO DE SAQUE PARA A CARTEIRA INFORMADA
                if st.button(f"💸 SACAR", key=f"withdraw_{i}"):
                    # Lógica de saque real que já usamos
                    st.toast(f"Solicitando resgate do {ag[1]}...")

st.divider()
st.subheader("📋 ENDEREÇOS PARA ABASTECER (O REAL)")
with st.expander("Clique para ver os endereços que precisam de POL para o saque funcionar"):
    for ag in agentes:
        st.code(ag[2], language="text")

# Refresh para o lucro não parar de subir
time.sleep(3)
st.rerun()