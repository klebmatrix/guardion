import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. SETUP ---
st.set_page_config(page_title="GUARDION OMNI v15.2 REAL", layout="wide")

db = sqlite3.connect('guardion_real_v15.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

agentes = db.execute("SELECT * FROM agentes").fetchall()

# --- 2. LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🛡️ QG GUARDION REAL")
    senha = st.text_input("Chave Mestre:", type="password")
    if st.button("DESBLOQUEAR"):
        if senha == st.secrets.get("SECRET_KEY", "mestre2026"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 3. CONEXÃO BLOCKCHAIN ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def pegar_preco_btc():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price'])
    except: return None

# ABASTECIMENTO FORÇADO (CORREÇÃO DE NONCE)
def abastecer_agentes(pk_mestre):
    try:
        mestre_acc = Account.from_key(pk_mestre)
        # Tenta abastecer os primeiros 5 snipers para garantir sucesso
        alvo_agentes = db.execute("SELECT endereco FROM agentes LIMIT 5").fetchall()
        
        # Pega o Nonce considerando transações que ainda estão na fila (pending)
        current_nonce = w3.eth.get_transaction_count(mestre_acc.address, 'pending')
        
        for ag in alvo_agentes:
            gas_price = int(w3.eth.gas_price * 1.5) # Taxa 50% maior para urgência
            tx = {
                'nonce': current_nonce,
                'to': ag[0],
                'value': w3.to_wei(1.0, 'ether'), # Enviando 1 POL para garantir o gás
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, pk_mestre)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            current_nonce += 1 # Pula para o próximo nonce imediatamente
            time.sleep(0.5)
        return True
    except Exception as e:
        st.sidebar.error(f"Erro de Rede: {str(e)}")
        return False

# --- 4. LÓGICA DE OPERAÇÃO ---
st.title("🛡️ COMMANDER OMNI v15.2")
btc = pegar_preco_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    for ag in