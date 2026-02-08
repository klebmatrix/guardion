import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# CONEXÃO REAL (POLYGON)
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v33.0 - FIX", layout="wide")

# --- DATABASE COM NOVO NOME PARA EVITAR CONFLITO ---
db = sqlite3.connect('guardion_final_v33.db', check_same_thread=False)
# Criamos a tabela com 5 colunas exatas
db.execute('''CREATE TABLE IF NOT EXISTS tropa 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, lucro_acumulado REAL)''')
db.commit()

# --- MOTOR VISUAL ---
if "preco_v33" not in st.session_state: st.session_state.preco_v33 = 98000.0
if "global_profit" not in st.session_state: st.session_state.global_profit = 0.0

variacao = random.uniform(-100.0, 150.0)
st.session_state.preco_v33 += variacao
if variacao > 0:
    st.session_state.global_profit += random.uniform(5.0, 30.0)

# --- FUNÇÃO DE SAQUE ---
def executar_saque_real(privada_origem, carteira_destino):
    try:
        conta = Account.from_key(privada_origem)
        saldo_wei = W3.eth.get_balance(conta.address)
        gas_price = int(W3.eth.gas_price * 1.5)
        taxa = gas_price * 21000
        valor_final = saldo_wei - taxa
        if valor_final > 0:
            tx = {'nonce': W3.eth.get_transaction_count(conta.address), 'to': W3.to_checksum_address(carteira_destino),
                  'value': valor_final, 'gas': 21000, 'gasPrice': gas_price, 'chainId': 137}
            signed = W3.eth.account.sign_transaction(tx, privada_origem)
            tx_hash = W3.eth.send_raw_transaction(signed.raw_transaction)
            return f"✅ SUCESSO! Hash: {W3.to_hex(tx_hash)[:10]}"
        return "❌ SEM SALDO POL"
    except Exception as e: return f"❌ ERRO: {str(e)}"

# --- INTERFACE ---
st.title("🛡️ PAINEL AGENTES - VERSÃO CORRIGIDA")

c1, c2, c3 = st.columns(3)
c1.metric("PREÇO", f"${st.session_state.preco_v33:,.2f}", f"{variacao:.2f}")
c2.metric("LUCRO ACUMULADO", f"${st.session_state.global_profit:,.2f}")
c3.metric("META", "$10,000.00")

with st.sidebar:
    st.header("🎯 DESTINO")
    minha_wallet = st.text_input("Sua MetaMask:", value="0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe")
    if st.button("🔥 RESETAR E GERAR 10 AGENTES"):
        db.execute("DELETE FROM tropa")
        for i in range(10):
            acc = Account.create()
            # AGORA OS 5 VALORES BATEM COM AS 5 COLUNAS
            db.execute("INSERT INTO tropa (id, nome, endereco, privada, lucro_acumulado) VALUES (?,?,?,?,?)", 
                       (i, f"AGENTE-{i+1:02d}", acc.address, acc.key.hex(), 0.0))
        db.commit()
        st.rerun()

# --- EXIBIÇÃO ---
agentes = db.execute("SELECT * FROM tropa").fetchall()
if agentes:
    cols = st.columns(5)
    for i, ag in enumerate(agentes):
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"🕵️ **{ag[1]}**")
                st.write(f"Lucro: :green[${(st.session_state.global_profit/10):,.2f}]")
                if st.button(f"💸 SACAR", key=f"w_{i}"):
                    st.info(executar_saque_real(ag[3], minha_wallet))

time.sleep(4)
st.rerun()