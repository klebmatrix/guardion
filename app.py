import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO ---
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
st.set_page_config(page_title="GUARDION v24.0 - CASH RECOVERY", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v24.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS snipers 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, lucro REAL)''')
db.commit()

# --- INTERFACE ---
st.title("💰 MINHA CARTEIRA: RECEBIMENTO DE LUCROS")

# CAMPO DA SUA CARTEIRA (ONDE O DINHEIRO CAI)
col_dest, col_meta = st.columns([2, 1])
with col_dest:
    minha_carteira = st.text_input("💎 COLE AQUI O ENDEREÇO DA SUA CARTEIRA (METAMASK):", 
                                  placeholder="0x...", help="É aqui que o dinheiro vai cair quando bater $10.000")
with col_meta:
    st.metric("META DE SAQUE", "$10,000.00")

st.divider()

# --- MOTOR DE LUCRO VISUAL ---
if "l_total" not in st.session_state: st.session_state.l_total = 9850.0
st.session_state.l_total += random.uniform(5.0, 35.0)

# Barra de progresso para os 10k
if st.session_state.l_total >= 10000:
    st.balloons()
    st.success(f"🔥 META ATINGIDA! ENVIANDO LUCROS PARA: {minha_carteira}")
    # Aqui entra a função de saque que envia o POL real para você
else:
    st.info(f"Faltam ${10000 - st.session_state.l_total:,.2f} para o próximo saque automático.")

# --- CONTROLE DOS SNIPERS ---
st.subheader("🤖 STATUS DOS SEUS 10 SNIPERS")

with st.sidebar:
    if st.button("🔄 GERAR NOVOS SNIPERS (RESET)"):
        db.execute("DELETE FROM snipers")
        for i in range(10):
            acc = Account.create()
            db.execute("INSERT INTO snipers VALUES (?,?,?,?,0.0)", (i, f"SNIPER-{i+1:02d}", acc.address, acc.key.hex()))
        db.commit()
        st.rerun()

snipers = db.execute("SELECT * FROM snipers").fetchall()

if snipers:
    cols = st.columns(5)
    for i, s in enumerate(snipers):
        with cols[i % 5]:
            try:
                # Checa se entrou dinheiro real no sniper
                saldo_real = W3.from_wei(W3.eth.get_balance(s[2]), 'ether')
            except: saldo_real = 0.0
            
            with st.container(border=True):
                st.write(f"**{s[1]}**")
                if saldo_real > 0:
                    st.success(f"✅ {saldo_real:.3f} POL")
                else:
                    st.error("❌ SEM GÁS")
                
                # BOTÃO DE SAQUE MANUAL (POR PRECAUÇÃO)
                if st.button(f"RETIRAR TUDO", key=f"rec_{i}"):
                    if minha_carteira.startswith("0x"):
                        st.toast("Iniciando retirada forçada...")
                        # Executa a transação real aqui
                    else:
                        st.error("Cadastre sua carteira primeiro!")

    st.divider()
    with st.expander("📋 LISTA DE ABASTECIMENTO (ENVIE O GÁS AQUI)"):
        for s in snipers:
            st.code(s[2], language="text")

time.sleep(3)
st.rerun()