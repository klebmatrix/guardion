import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- RPCs ROBUSTOS (TESTE DE CONEXÃO) ---
RPCS = ["https://polygon.llamarpc.com", "https://rpc.ankr.com/polygon"]
W3 = Web3(Web3.HTTPProvider(RPCS[0]))

st.set_page_config(page_title="GUARDION v18.2 - BYPASS", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_bypass.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT)''')
db.commit()

st.title("🛡️ COMMANDER v18.2 | MODO ANTI-BLOQUEIO")
st.info("O erro 403 ocorreu porque os servidores públicos bloqueiam robôs. Vamos usar o modo de 'Abastecimento Direto'.")

# --- 1. GERADOR DE CARTEIRAS ---
if st.button("🔄 PASSO 1: GERAR/RESETAR 20 SNIPERS (MODO ESTÁVEL)"):
    db.execute("DELETE FROM agentes")
    # Reduzido para 20 para garantir que a rede não te barre
    for i in range(20):
        acc = Account.create()
        db.execute("INSERT INTO agentes (id, nome, endereco, privada) VALUES (?,?,?,?)",
                   (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex()))
    db.commit()
    st.rerun()

snipers = db.execute("SELECT * FROM agentes").fetchall()

if snipers:
    st.divider()
    st.subheader("⛽ PASSO 2: ABASTECIMENTO MANUAL (SEM ERRO 403)")
    st.write("Para evitar o bloqueio da rede, envie **0.5 POL** para os endereços abaixo diretamente da sua MetaMask.")
    
    # Criando um CSV ou lista para facilitar
    lista_ends = [s[2] for s in snipers]
    st.text_area("Copie todos os endereços aqui:", value="\n".join(lista_ends), height=150)
    
    st.divider()
    st.subheader("📊 MONITOR DE SALDO (REAL-TIME)")
    
    
    
    cols = st.columns(4)
    for i, s in enumerate(snipers):
        with cols[i % 4]:
            with st.container(border=True):
                st.write(f"**{s[1]}**")
                st.caption(f"`{s[2]}`")
                if st.button(f"Checar ⛽", key=f"check_{s[0]}"):
                    try:
                        bal = W3.from_wei(W3.eth.get_balance(s[2]), 'ether')
                        if bal > 0: st.success(f"{bal:.3f} POL")
                        else: st.error("0.00 POL")
                    except: st.warning("Rede Ocupada")

# --- MOTOR DE PREÇO (SIMULADO PARA NÃO TRAVAR O IP) ---
if "p" not in st.session_state: st.session_state.p = 98000.0
st.session_state.p += st.session_state.p * random.uniform(-0.003, 0.003)
st.sidebar.metric("PREÇO ATUAL", f"${st.session_state.p:,.2f}")

time.sleep(10)
st.rerun()