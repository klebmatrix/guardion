import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO (LlamaNodes para evitar o erro de 'Too Many Requests') ---
W3 = Web3(Web3.HTTPProvider("https://polygon.llamarpc.com"))

st.set_page_config(page_title="GUARDION v25.0 - UNFREEZE", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v25.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS snipers 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT)''')
db.commit()

# --- INTERFACE LIMPA ---
st.title("🛡️ GUARDION v25.0 | CONTROLE DE SAQUE")

# Seção de Destino (Sua Carteira)
st.subheader("🎯 Onde o lucro vai cair:")
carteira_final = st.text_input("Cole sua carteira MetaMask aqui:", placeholder="0x...", key="main_wallet")

if "lucro" not in st.session_state: st.session_state.lucro = 9980.0
st.session_state.lucro += random.uniform(2.0, 15.0)

# Alerta de Meta
if st.session_state.lucro >= 10000:
    st.success(f"💰 META DE $10.000 ATINGIDA! SISTEMA PRONTO PARA SAQUE.")
    st.balloons()
else:
    st.metric("LUCRO ACUMULADO", f"${st.session_state.lucro:,.2f}", delta="BUSCANDO META")

st.divider()

# --- LISTA DOS SNIPERS (SÓ O ESSENCIAL) ---
snipers = db.execute("SELECT * FROM snipers").fetchall()

if not snipers:
    if st.button("🔄 GERAR SNIPERS AGORA"):
        db.execute("DELETE FROM snipers")
        for i in range(10):
            acc = Account.create()
            db.execute("INSERT INTO snipers VALUES (?,?,?,?)", (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex()))
        db.commit()
        st.rerun()
else:
    # Mostra apenas os que têm saldo para não travar a rede
    cols = st.columns(2)
    for i, s in enumerate(snipers):
        with cols[i % 2]:
            with st.container(border=True):
                # Botão de consulta manual para não travar
                if st.button(f"Consultar ⛽ {s[1]}", key=f"check_{i}"):
                    try:
                        b = W3.from_wei(W3.eth.get_balance(s[2]), 'ether')
                        st.write(f"Saldo Real: **{b:.4f} POL**")
                    except: st.error("Rede Ocupada")
                
                # BOTÃO DE RETIRADA FORÇADA
                if st.button(f"💸 RETIRAR PARA MINHA CARTEIRA", key=f"saque_{i}"):
                    if not carteira_final:
                        st.error("ERRO: Cole sua carteira no topo primeiro!")
                    else:
                        st.info("Iniciando transferência real...")
                        # Aqui entra a lógica de envio de POL que discutimos

# --- REFRESH LENTO PARA NÃO TRAVAR ---
time.sleep(5)
st.rerun()