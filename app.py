import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO ---
RPC_POLYGON = "https://polygon-rpc.com"
W3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

st.set_page_config(page_title="GUARDION v17.6 - GAS SYSTEM", layout="wide")

# --- BANCO DE DADOS ---
db = sqlite3.connect('guardion_v17_6.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, p_compra REAL, lucro_acumulado REAL, hash_saque TEXT)''')
db.commit()

# --- FUNÇÃO: DISTRIBUIÇÃO ---
def distribuir_combustivel(pk_mestra, lista_agentes):
    try:
        conta_mestra = Account.from_key(pk_mestra)
        status_box = st.empty()
        for i, ag in enumerate(lista_agentes):
            status_box.info(f"⛽ Abastecendo {ag[1]} ({i+1}/50)...")
            tx = {
                'nonce': W3.eth.get_transaction_count(conta_mestra.address),
                'to': ag[2],
                'value': W3.to_wei(0.15, 'ether'),
                'gas': 21000,
                'gasPrice': W3.eth.gas_price,
                'chainId': 137
            }
            assinada = W3.eth.account.sign_transaction(tx, pk_mestra)
            W3.eth.send_raw_transaction(assinada.raw_transaction)
            time.sleep(0.4) 
        st.success("✅ TODA A TROPA FOI ABASTECIDA!")
    except Exception as e:
        st.error(f"Erro Crítico: {e}")

# --- CABEÇALHO DE COMANDO ---
st.title("🛡️ PAINEL DE ABASTECIMENTO REAL")

# Botão de Reset/Geração de Carteiras (Sempre visível)
if st.button("🔄 1. GERAR/RESETAR 50 CARTEIRAS DE SNIPERS"):
    db.execute("DELETE FROM agentes")
    for i in range(50):
        acc = Account.create()
        db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?)",
                   (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0, ""))
    db.commit()
    st.rerun()

st.divider()

# --- ÁREA DE ABASTECIMENTO (CENTRAL) ---
c1, c2 = st.columns(2)
with c1:
    pk_input = st.text_input("🔑 COLE SUA PRIVATE KEY AQUI (ONDE ESTÃO OS 10 POL):", type="password")
with c2:
    dest_input = st.text_input("🎯 SUA CARTEIRA DE DESTINO (PARA RECEBER O LUCRO):")

if st.button("🚀 2. EXECUTAR ABASTECIMENTO DA TROPA (ENVIAR GÁS)", use_container_width=True):
    if pk_input:
        lista = db.execute("SELECT * FROM agentes").fetchall()
        distribuir_combustivel(pk_input, lista)
    else:
        st.error("Você precisa colar a Private Key para o robô distribuir o gás!")

st.divider()

# --- MONITOR DE GÁS ---
agentes = db.execute("SELECT * FROM agentes").fetchall()
st.subheader("📋 MONITOR DE COMBUSTÍVEL EM TEMPO REAL")



cols = st.columns(5)
for i, a in enumerate(agentes):
    with cols[i % 5]:
        try:
            saldo = W3.from_wei(W3.eth.get_balance(a[2]), 'ether')
        except: saldo = 0.0
        
        with st.container(border=True):
            st.write(f"**{a[1]}**")
            st.code(a[2], language="text") # Endereço para cópia manual
            if saldo > 0.05:
                st.success(f"⛽ {saldo:.3f} POL")
            else:
                st.error("⛽ SEM GÁS")

# --- MOTOR DE PREÇO (PILOTO AUTOMÁTICO SEMPRE ON) ---
if "preco" not in st.session_state: st.session_state.preco = 98000.0
st.session_state.preco += st.session_state.preco * random.uniform(-0.005, 0.005)
st.sidebar.metric("PREÇO ATUAL", f"${st.session_state.preco:,.2f}")

time.sleep(3)
st.rerun()