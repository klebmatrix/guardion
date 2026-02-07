import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# --- CAMPO DE CHAVE NO PAINEL (SUBSTITUI O SECRETS) ---
with st.sidebar:
    st.header("🔐 Autenticação")
    # O valor fica guardado apenas enquanto a aba estiver aberta
    pk_input = st.text_input("Insira a sua PK_01 (Mestre):", type="password", help="A chave não será salva no servidor, apenas na sessão atual.")
    
    if pk_input:
        try:
            # Limpeza da chave
            pk_limpa = pk_input.strip().replace('"', '')
            if not pk_limpa.startswith("0x") and len(pk_limpa) == 64:
                pk_limpa = "0x" + pk_limpa
            
            acc_mestre = Account.from_key(pk_limpa)
            PK_MESTRE = pk_limpa
            st.success(f"✅ Ligado: {acc_mestre.address[:6]}...{acc_mestre.address[-4:]}")
            
            s_mestre = round(w3.from_wei(w3.eth.get_balance(acc_mestre.address), 'ether'), 2)
            st.metric("Saldo Mestre", f"{s_mestre} POL")
        except:
            st.error("❌ Chave Inválida")
            PK_MESTRE = None
    else:
        PK_MESTRE = None
        st.warning("⚠️ Insira a PK para ativar o reabastecimento.")

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('guardion_data.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    status TEXT, ultima_acao TEXT, data_criacao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- LOGÍSTICA ---
def auto_abastecer(addr):
    if not PK_MESTRE: return
    try:
        if w3.eth.get_balance(addr) < w3.to_wei(0.1, 'ether'):
            acc_m = Account.from_key(PK_MESTRE)
            tx = {
                'nonce': w3.eth.get_transaction_count(acc_m.address),
                'to': addr, 'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            st.toast(f"⛽ Gas enviado para {addr[:6]}")
    except: pass

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v10.6")

agentes = db.execute("SELECT * FROM modulos").fetchall()

with st.sidebar:
    st.divider()
    st.header("🏭 Fábrica de Grid")
    qtd = st.select_slider("Soldados:", options=[1, 5, 10, 25], value=25)
    p_topo = st.number_input("Preço Topo:", value=102500.0)
    
    if st.button(f"🚀 LANÇAR {qtd} AGENTES"):
        novos = []
        for i in range(qtd):
            acc = Account.create()
            p_alvo = p_topo - (i * 200)
            novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_alvo, 0.0, 10.0, 5.0, "VIGILANCIA", f"Alvo ${p_alvo}", datetime.now().strftime("%H:%M")))
        db.executemany("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, status, ultima_acao, data_criacao) VALUES (?,?,?,?,?,?,?,?,?,?)", novos)
        db.commit()
        st.rerun()

# Painel de Agentes
if agentes:
    cols = st.columns(4)
    for idx, ag in enumerate(agentes):
        with cols[idx % 4]:
            with st.container(border=True):
                s_pol = round(w3.from_wei(w3.eth.get_balance(ag[2]), 'ether'), 3)
                st.write(f"**{ag[1]}**")
                st.progress(min(s_pol / 0.5, 1.0))
                st.caption(f"Saldo: {s_pol} POL")
                if PK_MESTRE: auto_abastecer(ag[2])
else:
    st.info("Sistema pronto. Insira a PK na lateral e lance os agentes.")

time.sleep(30)
st.rerun()