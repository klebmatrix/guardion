import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, os, secrets
import pandas as pd
from datetime import datetime

# 1. Configurações Iniciais
st.set_page_config(page_title="GUARDION OMNI v6.0", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# 2. Segurança: Puxa a chave mestre dos Secrets do Streamlit
PK_MESTRE = st.secrets.get("PK_MESTRE")

# 3. Banco de Dados
def init_db():
    conn = sqlite3.connect('guardion_data.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    stop_loss REAL, status TEXT, ultima_acao TEXT, data_criacao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# 4. Função: Reabastecimento Automático (O Míssil Inteligente)
def verificar_e_abastecer(endereco_agente):
    if not PK_MESTRE: return
    try:
        acc_mestre = Account.from_key(PK_MESTRE)
        saldo = w3.eth.get_balance(endereco_agente)
        limite = w3.to_wei(0.1, 'ether') # 0.1 POL é o alerta
        
        if saldo < limite:
            nonce = w3.eth.get_transaction_count(acc_mestre.address)
            tx = {
                'nonce': nonce, 'to': endereco_agente, 'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            st.toast(f"⛽ Agente {endereco_agente[:6]} reabastecido automaticamente!")
    except: pass

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI | AUTONOMIA TOTAL")

# 5. Carregar Agentes (CORRIGE O NAMEERROR)
cursor = db.cursor()
agentes = cursor.execute("SELECT * FROM modulos").fetchall()

# 6. Dashboard de Status
c1, c2, c3 = st.columns(3)
c1.metric("Exército Ativo", len(agentes))
c2.metric("Sistema de Combustível", "AUTÔNOMO" if PK_MESTRE else "MANUAL")
c3.metric("Status da Missão", "Vigilância Ativa")



# --- MONITORAMENTO E EXECUÇÃO ---
if agentes:
    tabs = st.tabs(["🎯 Alvos", "🔥 Combate", "📊 Log"])
    
    with tabs[0]: # ABA VIGILÂNCIA
        for ag in agentes:
            id_m, nome, addr, priv, alvo, p_gat, p_comp, lucro, stop, status, acao, data = ag
            
            if status == "VIGILANCIA":
                # Verificação de Gás em tempo real
                verificar_e_abastecer(addr)
                
                with st.expander(f"🤖 {nome} | Vigilando {alvo}"):
                    st.write(f"Endereço: `{addr}`")
                    # Lógica de preço aqui...
    
    with tabs[1]: # ABA COMBATE
        for ag in agentes:
            if ag[9] == "POSICIONADO":
                st.warning(f"🚀 {ag[1]} em operação no ativo {ag[4]}")
                verificar_e_abastecer(ag[2]) # Garante gás para a venda!

else:
    st.info("Aguardando recrutamento de agentes na barra lateral.")

# 7. Sidebar: Fábrica de Batalhão
with st.sidebar:
    st.header("🏭 Fábrica de Agentes")
    if st.button("GERAR NOVO AGENTE"):
        acc = Account.create()
        db.execute("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, status, data_criacao) VALUES (?,?,?,?,?,?,?)",
                   (f"SNPR-{secrets.token_hex(2).upper()}", acc.address, acc.key.hex(), "WBTC", 45000.0, "VIGILANCIA", datetime.now().strftime("%H:%M")))
        db.commit()
        st.rerun()

# Auto-refresh
time.sleep(60)
st.rerun()