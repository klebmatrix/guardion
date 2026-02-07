import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO DIRETA ---
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v17.9 - FORCE START", layout="wide")

# --- DATABASE (LIMPEZA TOTAL) ---
db = sqlite3.connect('guardion_force.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, p_compra REAL, lucro_real REAL)''')
db.commit()

# --- FUNÇÃO DE ABASTECIMENTO ---
def forcar_abastecimento(pk_origem, lista_snipers):
    try:
        conta = Account.from_key(pk_origem)
        progresso = st.progress(0)
        for i, sniper in enumerate(lista_snipers):
            st.toast(f"Abastecendo {sniper[1]}...")
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address),
                'to': sniper[2],
                'value': W3.to_wei(0.15, 'ether'),
                'gas': 21000,
                'gasPrice': int(W3.eth.gas_price * 1.5),
                'chainId': 137
            }
            assinada = W3.eth.account.sign_transaction(tx, pk_origem)
            W3.eth.send_raw_transaction(assinada.raw_transaction)
            time.sleep(2.0) # Pausa obrigatória anti-bloqueio
            progresso.progress((i + 1) / len(lista_snipers))
        st.success("✅ ABASTECIMENTO CONCLUÍDO!")
    except Exception as e:
        st.error(f"ERRO: {e}")

# --- INTERFACE ---
st.title("🛡️ GUARDION v17.9 - COMANDO DE FORÇA")

# 1. BOTÃO DE EMERGÊNCIA (CLIQUE AQUI PRIMEIRO)
if st.button("🚨 1. CLIQUE AQUI PARA GERAR AS 50 CARTEIRAS", use_container_width=True):
    db.execute("DELETE FROM agentes")
    for i in range(50):
        acc = Account.create()
        db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?)",
                   (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0))
    db.commit()
    st.rerun()

st.divider()

# 2. CAMPOS DE DADOS
col1, col2 = st.columns(2)
with col1:
    pk = st.text_input("🔑 CHAVE PRIVADA (ORIGEM):", type="password")
with col2:
    destino = st.text_input("🎯 CARTEIRA PARA RECEBER LUCRO:")

# 3. BOTÃO DE ABASTECER
snipers = db.execute("SELECT * FROM agentes").fetchall()
if st.button("🚀 2. DISTRIBUIR GÁS AGORA", use_container_width=True):
    if pk and snipers:
        forcar_abastecimento(pk, snipers)
    else:
        st.error("ERRO: Gere as carteiras no botão acima ou insira a Chave Privada!")

st.divider()

# --- MONITOR ---
st.subheader("📊 STATUS DA TROPA")
if not snipers:
    st.warning("⚠️ Nenhuma carteira gerada. Clique no botão 1 acima.")
else:
    cols = st.columns(5)
    for i, s in enumerate(snipers):
        with cols[i % 5]:
            try:
                saldo = W3.from_wei(W3.eth.get_balance(s[2]), 'ether')
            except: saldo = 0.0
            with st.container(border=True):
                st.write(f"**{s[1]}**")
                st.caption(f"End: {s[2][:6]}...{s[2][-4:]}")
                if saldo > 0.1: st.success(f"⛽ {saldo:.3f} POL")
                else: st.error("⛽ SEM GÁS")

time.sleep(5)
st.rerun()