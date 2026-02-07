import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO RPC ---
st.set_page_config(page_title="GUARDION RECOVERY", layout="wide")
RPC_URL = "https://polygon-rpc.com" 
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- BANCO DE DADOS (COM TRATAMENTO DE TRAVAMENTO) ---
def init_db():
    try:
        # Tenta conectar ao banco atual
        conn = sqlite3.connect('guardion_data_v2.db', check_same_thread=False, timeout=10)
        conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                        (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                        alvo REAL, status TEXT, ultima_acao TEXT)''')
        conn.commit()
        return conn
    except:
        st.error("🚨 O Banco de Dados travou. Tentando recuperação automática...")
        return None

db = init_db()

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI | RECOVERY v10.8")

with st.sidebar:
    st.header("🔐 Autenticação")
    pk_input = st.text_input("Sua PK_01:", type="password")
    
    st.divider()
    st.header("⚙️ Comandos de Emergência")
    if st.button("🗑️ APAGAR TUDO E REINICIAR"):
        if db:
            db.execute("DELETE FROM modulos")
            db.commit()
            st.rerun()

# --- LÓGICA DE LANÇAMENTO ---
if st.sidebar.button("🚀 LANÇAR 25 NOVOS AGENTES"):
    if db:
        novos = []
        p_topo = 102500.0
        for i in range(25):
            acc = Account.create()
            p_alvo = p_topo - (i * 200)
            novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_alvo, "VIGILANCIA", "Aguardando"))
        
        try:
            db.executemany("INSERT INTO modulos (nome, endereco, privada, alvo, status, ultima_acao) VALUES (?,?,?,?,?,?)", novos)
            db.commit()
            st.success("25 Agentes criados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- MONITOR ---
if db:
    agentes = db.execute("SELECT * FROM modulos").fetchall()
    if agentes:
        st.subheader(f"📡 Batalhão Ativo ({len(agentes)} Agentes)")
        df = pd.DataFrame(agentes, columns=['ID', 'Nome', 'Endereço', 'Privada', 'Alvo', 'Status', 'Ação'])
        st.dataframe(df.drop(columns=['Privada']), use_container_width=True)
    else:
        st.info("Nenhum agente no banco de dados.")

# Pausa para não estressar o servidor
time.sleep(30)