import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v16.4", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"
W3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

# --- BANCO DE DADOS ---
db = sqlite3.connect('guardion_v16_4.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            alvo REAL, status TEXT, preco_compra REAL, lucro_real REAL, hash TEXT)''')
db.commit()

# --- FUNÇÃO DE SAQUE (RETIRAR) ---
def realizar_saque_total(endereco_destino):
    st.warning(f"Iniciando retirada para {endereco_destino}...")
    agentes = db.execute("SELECT endereco, privada, nome FROM agentes").fetchall()
    sucesso = 0
    for end_ag, priv_ag, nome in agentes:
        try:
            saldo = W3.eth.get_balance(end_ag)
            if saldo > W3.to_wei(0.02, 'ether'):
                tx = {
                    'nonce': W3.eth.get_transaction_count(end_ag),
                    'to': endereco_destino,
                    'value': saldo - W3.to_wei(0.01, 'ether'), # Deixa taxa de gás
                    'gas': 21000,
                    'gasPrice': W3.eth.gas_price,
                    'chainId': 137
                }
                assinado = W3.eth.account.sign_transaction(tx, priv_ag)
                W3.eth.send_raw_transaction(assinado.raw_transaction)
                sucesso += 1
        except: continue
    st.success(f"Saque concluído! {sucesso} agentes enviaram fundos.")

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI | OPERAÇÃO DE RESGATE")

if "preco" not in st.session_state: st.session_state.preco = 96000.0

with st.sidebar:
    st.header("🎮 PAINEL DE CONTROLE")
    st.session_state.preco += st.session_state.preco * random.uniform(-0.002, 0.002)
    st.metric("Preço SIN", f"${st.session_state.preco:,.2f}")
    
    st.divider()
    st.subheader("💰 ÁREA DE RETIRADA")
    carteira_mestra = st.text_input("Endereço de Destino (Sua Carteira):", placeholder="0x...")
    
    if st.button("🏦 RESGATAR LUCROS (SAQUE TOTAL)"):
        if Web3.is_address(carteira_mestra):
            realizar_saque_total(carteira_mestra)
        else:
            st.error("Endereço Inválido! Insira sua carteira 0x...")

    st.divider()
    if st.button("🚀 REINICIAR GRID"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), st.session_state.preco, "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- MONITOR ---
agentes = db.execute("SELECT * FROM agentes").fetchall()
st.subheader(f"💵 Lucro Total Disponível: :green[${sum([a[7] for a in agentes]):,.2f}]")



cols = st.columns(5)
for i, a in enumerate(agentes):
    with cols[i % 5]:
        with st.container(border=True):
            st.write(f"**{a[1]}**")
            st.write(f"Lucro: ${a[7]:,.2f}")
            st.caption(f"Status: {a[5]}")

time.sleep(4)
st.rerun()