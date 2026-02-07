import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO ESTÁVEL (LlamaNodes é mais resiliente) ---
W3 = Web3(Web3.HTTPProvider("https://polygon.llamarpc.com"))

st.set_page_config(page_title="GUARDION v18.5 - STATUS REAL", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v18_5.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, status TEXT)''')
db.commit()

st.title("🛡️ MONITOR DE OPERAÇÃO AUTOMÁTICA")

# --- ÁREA DE COMANDO ---
with st.sidebar:
    st.header("🎮 COMANDOS")
    if st.button("🔄 1. GERAR TROPA (20 SNIPERS)"):
        db.execute("DELETE FROM agentes")
        for i in range(20):
            acc = Account.create()
            db.execute("INSERT INTO agentes (id, nome, endereco, privada, status) VALUES (?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "IDLE"))
        db.commit()
        st.rerun()
    
    st.divider()
    pilot_on = st.toggle("🚀 PILOTO AUTOMÁTICO", value=True)
    st.info("O Piloto Automático só vende se houver GÁS (POL) no sniper.")

# --- LISTA DE ABASTECIMENTO ---
snipers = db.execute("SELECT * FROM agentes").fetchall()

if not snipers:
    st.warning("⚠️ Nenhuma carteira encontrada. Clique em 'GERAR TROPA' no menu lateral.")
else:
    st.subheader("⛽ STATUS DE ABASTECIMENTO (POL)")
    st.write("Envie **0.2 POL** para os endereços abaixo para ativar o automático.")
    
    # Grid de visualização rápida
    cols = st.columns(5)
    for i, s in enumerate(snipers):
        with cols[i % 5]:
            # Consulta de saldo com tratamento de erro para não travar a tela
            try:
                # Só consulta se a rede estiver livre
                saldo = W3.from_wei(W3.eth.get_balance(s[2]), 'ether')
            except:
                saldo = -1 # Erro de conexão
            
            with st.container(border=True):
                st.write(f"**{s[1]}**")
                st.caption(f"`{s[2][:6]}...{s[2][-4:]}`")
                
                if saldo > 0.05:
                    st.success(f"⛽ {saldo:.3f} POL")
                    st.write("✅ **PRONTO**")
                elif saldo == -1:
                    st.warning("⏳ BUSCANDO...")
                else:
                    st.error("❌ **SEM GÁS**")

    st.divider()
    
    # --- ÁREA DE COPIAR (PARA FACILITAR O ABASTECIMENTO) ---
    with st.expander("📋 COPIAR TODOS OS ENDEREÇOS (PARA MANDAR GAS)"):
        ends = [x[2] for x in snipers]
        st.text_area("Endereços:", value="\n".join(ends), height=200)

# --- MOTOR DE PREÇO ---
if "p" not in st.session_state: st.session_state.p = 98000.0
if pilot_on:
    st.session_state.p += st.session_state.p * random.uniform(-0.002, 0.002)

st.sidebar.metric("PREÇO ATUAL", f"${st.session_state.p:,.2f}")

# Refresh automático mais longo para evitar o bloqueio da rede
time.sleep(10)
st.rerun()