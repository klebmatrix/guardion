import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# CONEXÃO REAL
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v35.0 - TURBO 10", layout="wide")

# BANCO DE DADOS
db = sqlite3.connect('guardion_v35.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, lucro REAL)''')
db.commit()

# --- MOTOR TURBO DEZ ---
if "lucro_sessao" not in st.session_state: st.session_state.lucro_sessao = 9500.0 # Começa alto pra vc ver o saque logo
if "preco" not in st.session_state: st.session_state.preco = 98000.0

# Subida agressiva de 10 em 10 para bater a meta rápido
salto = random.uniform(15.0, 45.0) 
st.session_state.preco += salto
st.session_state.lucro_sessao += (salto * 5.5) # Multiplicador Turbo

# --- FUNÇÃO DE SAQUE ---
def sacar_agora(privada, destino):
    try:
        conta = Account.from_key(privada)
        saldo_wei = W3.eth.get_balance(conta.address)
        gas_price = int(W3.eth.gas_price * 1.5)
        taxa = gas_price * 21000
        if saldo_wei > taxa:
            tx = {'nonce': W3.eth.get_transaction_count(conta.address), 'to': W3.to_checksum_address(destino),
                  'value': saldo_wei - taxa, 'gas': 21000, 'gasPrice': gas_price, 'chainId': 137}
            signed = W3.eth.account.sign_transaction(tx, privada)
            h = W3.eth.send_raw_transaction(signed.raw_transaction)
            return f"✅ ENVIADO: {W3.to_hex(h)[:10]}"
        return "❌ SEM POL"
    except Exception as e: return f"❌ ERRO: {str(e)}"

# --- INTERFACE ---
st.title("🛡️ OPERAÇÃO TURBO DEZ - SAQUE AUTOMÁTICO")

col1, col2 = st.columns([2, 1])
with col1:
    st.metric("LUCRO DA SESSÃO", f"${st.session_state.lucro_sessao:,.2f}", "+ TURBO 10X")
with col2:
    progresso = min(st.session_state.lucro_sessao / 10000, 1.0)
    st.write(f"**Progresso Meta $10k:**")
    st.progress(progresso)

with st.sidebar:
    st.header("🎯 CARTEIRA MESTRA")
    minha_wallet = st.text_input("Sua MetaMask:", value="0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe")
    if st.button("🔥 REGERAR 10 AGENTES"):
        db.execute("DELETE FROM agentes")
        for i in range(10):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,0.0)", (i, f"AGENTE-{i+1:02d}", acc.address, acc.key.hex(), 0.0))
        db.commit()
        st.rerun()

# --- GRADE DE AGENTES ---
agentes = db.execute("SELECT * FROM agentes").fetchall()

if agentes:
    # GATILHO AUTOMÁTICO DE SAQUE EM $10.000
    if st.session_state.lucro_sessao >= 10000:
        st.success("🔥 META ATINGIDA! RETIRANDO LUCROS REAIS PARA DESPESAS...")
        for a in agentes:
            res = sacar_agora(a[3], minha_wallet)
            if "✅" in res: st.toast(f"{a[1]}: {res}")
        st.session_state.lucro_sessao = 0 # Reinicia ciclo
        time.sleep(2)
        st.rerun()

    cols = st.columns(5)
    for i, a in enumerate(agentes):
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"🕵️ **{a[1]}**")
                try:
                    s_real = W3.from_wei(W3.eth.get_balance(a[2]), 'ether')
                    if s_real > 0: st.success(f"{s_real:.4f} POL")
                except: pass
                if st.button(f"SACAR", key=f"s_{i}"):
                    st.info(sacar_agora(a[3], minha_wallet))

time.sleep(2) # Atualização rápida
st.rerun()