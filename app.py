import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO (RPC MAIS RESISTENTE) ---
st.set_page_config(page_title="GUARDION OMNI", layout="wide")
# Trocando para o RPC da Cloudflare/Ankr que costuma ser mais estável
RPC_URL = "https://polygon-rpc.com" 
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- AUTENTICAÇÃO DIRETA ---
with st.sidebar:
    st.header("🔐 Autenticação")
    pk_input = st.text_input("Insira a sua PK_01:", type="password")
    
    if pk_input:
        try:
            pk_limpa = pk_input.strip().replace('"', '')
            if not pk_limpa.startswith("0x") and len(pk_limpa) == 64:
                pk_limpa = "0x" + pk_limpa
            acc_mestre = Account.from_key(pk_limpa)
            PK_MESTRE = pk_limpa
            st.success(f"✅ Conectado")
        except:
            st.error("❌ Chave Inválida")
            PK_MESTRE = None
    else:
        PK_MESTRE = None

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

# --- FUNÇÃO DE SALDO COM PROTEÇÃO (EVITA O ERRO HTTP) ---
def get_balance_safe(address):
    try:
        time.sleep(0.1) # Pequena pausa de 100ms entre requisições
        balance_wei = w3.eth.get_balance(address)
        return round(w3.from_wei(balance_wei, 'ether'), 3)
    except:
        return 0.0

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI v10.7")

agentes = db.execute("SELECT * FROM modulos").fetchall()

with st.sidebar:
    st.divider()
    if st.button("🚀 GERAR 25 AGENTES"):
        p_topo = 102500.0
        novos = []
        for i in range(25):
            acc = Account.create()
            p_alvo = p_topo - (i * 200)
            novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_alvo, 0.0, 10.0, 5.0, "VIGILANCIA", f"Alvo ${p_alvo}", datetime.now().strftime("%H:%M")))
        db.executemany("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, status, ultima_acao, data_criacao) VALUES (?,?,?,?,?,?,?,?,?,?)", novos)
        db.commit()
        st.rerun()
    
    if st.button("🧹 LIMPAR AGENTES"):
        db.execute("DELETE FROM modulos")
        db.commit()
        st.rerun()

# --- EXIBIÇÃO ---
if agentes:
    st.subheader("⛽ Status de Combustível")
    cols = st.columns(5) # 5 colunas para ficar organizado
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            # Chamando a função segura que evita o erro HTTP
            s_pol = get_balance_safe(ag[2])
            st.metric(ag[1], f"{s_pol} POL")
            st.caption(f"Alvo: ${ag[3]}")
else:
    st.info("Nenhum agente no campo. Use a lateral para lançar.")

# Refresh mais lento para não ser banido pelo RPC
time.sleep(60) 
st.rerun()