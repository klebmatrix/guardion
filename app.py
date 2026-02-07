import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, secrets
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GUARDION OMNI v10.0", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))
PK_MESTRE = st.secrets.get("PK_MESTRE")

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('guardion_data.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    stop_loss REAL, status TEXT, ultima_acao TEXT, data_criacao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- MOTOR DE LOGÍSTICA ---
def auto_abastecer(addr):
    if not PK_MESTRE: return
    try:
        acc_mestre = Account.from_key(PK_MESTRE)
        if w3.eth.get_balance(addr) < w3.to_wei(0.1, 'ether'):
            tx = {
                'nonce': w3.eth.get_transaction_count(acc_mestre.address),
                'to': addr, 'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            st.toast(f"⛽ Gas enviado: {addr[:6]}", icon="🚀")
    except: pass

def get_price(coin):
    try:
        ids = {"WBTC": "bitcoin", "ETH": "ethereum"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        return requests.get(url, timeout=5).json()[ids[coin]]['usd']
    except: return None

# --- INTERFACE DE COMANDO ---
st.title("🛡️ COMMANDER OMNI | GRID DASHBOARD")

# Carregar Agentes
agentes = db.execute("SELECT * FROM modulos").fetchall()

# Sidebar: Configuração da Rede
with st.sidebar:
    st.header("🏭 Fábrica de Grid")
    qtd = st.select_slider("Soldados:", options=[1, 5, 10, 25, 50], value=25)
    ativo = st.selectbox("Ativo", ["WBTC", "ETH"])
    p_topo = st.number_input("Preço Inicial (Topo):", value=102500.0)
    dist = st.number_input("Distância ($):", value=200.0)
    
    if st.button(f"🚀 LANÇAR {qtd} AGENTES"):
        novos = []
        for i in range(qtd):
            acc = Account.create()
            p_alvo = p_topo - (i * dist)
            novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), ativo, p_alvo, 
                          0.0, 10.0, 5.0, "VIGILANCIA", f"Aguardando ${p_alvo}", 
                          datetime.now().strftime("%H:%M")))
        db.executemany("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, stop_loss, status, ultima_acao, data_criacao) VALUES (?,?,?,?,?,?,?,?,?,?,?)", novos)
        db.commit()
        st.success("Rede Lançada!")
        st.rerun()

    if st.button("🧹 LIMPAR QG"):
        db.execute("DELETE FROM modulos")
        db.commit()
        st.rerun()

# Painel Principal
if agentes:
    # Gráfico do Grid
    st.subheader("📊 Visualização da Rede de Captura")
    vigi_df = pd.DataFrame([{"Agente": a[1], "Preço Gatilho": a[5]} for a in agentes if a[9] == "VIGILANCIA"])
    if not vigi_df.empty:
        st.line_chart(vigi_df.set_index("Agente"))

    t1, t2 = st.tabs(["🎯 Monitor", "📊 Histórico"])
    
    with t1:
        preco_atual = get_price(agentes[0][4])
        st.metric(f"Preço Atual {agentes[0][4]}", f"${preco_atual}")
        
        for ag in agentes:
            id_m, nome, addr, priv, alvo, p_gat, p_com, luc, stp, status, acao, data = ag
            if status == "VIGILANCIA":
                auto_abastecer(addr)
                if preco_atual and preco_atual <= p_gat:
                    db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao='COMPRADO' WHERE id=?", (preco_atual, id_m))
                    db.commit()
                    st.rerun()
            
            with st.expander(f"{nome} - {status} em ${p_gat}"):
                st.code(addr, language="text")
                st.write(f"Status: {acao}")

else:
    st.info("Aguardando lançamento da primeira rede de 25 agentes.")

# Ciclo de Vida
time.sleep(60)
st.rerun()