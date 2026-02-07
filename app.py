import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, secrets
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GUARDION OMNI v10.2", layout="wide")
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
        saldo_wei = w3.eth.get_balance(addr)
        if saldo_wei < w3.to_wei(0.1, 'ether'):
            tx = {
                'nonce': w3.eth.get_transaction_count(acc_mestre.address),
                'to': addr, 'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            st.toast(f"🚀 Míssil de Gás enviado para {addr[:6]}", icon="⛽")
    except: pass

def get_price(coin):
    try:
        ids = {"WBTC": "bitcoin", "ETH": "ethereum"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        return requests.get(url, timeout=5).json()[ids[coin]]['usd']
    except: return None

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI | SENTINEL v10.2")

# 1. MONITOR DA TESOURARIA MESTRE (OS SEUS 24 POL)
if PK_MESTRE:
    try:
        addr_mestre = Account.from_key(PK_MESTRE).address
        s_mestre_wei = w3.eth.get_balance(addr_mestre)
        s_mestre_pol = round(w3.from_wei(s_mestre_wei, 'ether'), 2)
        
        col_t1, col_t2 = st.columns([1, 3])
        with col_t1:
            st.metric("💰 Saldo Wallet Mestre", f"{s_mestre_pol} POL")
        
        with col_t2:
            if s_mestre_pol < 2.0:
                st.error(f"🚨 ALERTA CRÍTICO: Tesouraria com apenas {s_mestre_pol} POL! Recarregue a Wallet 01 urgentemente.")
            elif s_mestre_pol < 5.0:
                st.warning(f"⚠️ Atenção: Saldo de reserva a baixar ({s_mestre_pol} POL).")
            else:
                st.success(f"✅ Logística Operacional: {s_mestre_pol} POL disponíveis para abastecimento.")
    except:
        st.error("❌ Erro ao aceder à Wallet Mestre. Verifique a sua PK_MESTRE nos Secrets.")

st.divider()

agentes = db.execute("SELECT * FROM modulos").fetchall()

# Sidebar: Fábrica de Grid
with st.sidebar:
    st.header("🏭 Fábrica de Grid")
    qtd = st.select_slider("Soldados:", options=[1, 5, 10, 25, 50], value=25)
    ativo = st.selectbox("Ativo", ["WBTC", "ETH"])
    p_topo = st.number_input("Preço Inicial (Topo):", value=102500.0)
    dist = st.number_input("Distância ($):", value=200.0)
    
    if st.button(f"🚀 LANÇAR REDE DE {qtd} AGENTES"):
        novos = []
        for i in range(qtd):
            acc = Account.create()
            p_alvo = p_topo - (i * dist)
            novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), ativo, p_alvo, 
                          0.0, 10.0, 5.0, "VIGILANCIA", f"Vigiando em ${p_alvo}", 
                          datetime.now().strftime("%H:%M")))
        db.executemany("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, stop_loss, status, ultima_acao, data_criacao) VALUES (?,?,?,?,?,?,?,?,?,?,?)", novos)
        db.commit()
        st.success(f"Rede lançada com sucesso!")
        st.rerun()

    if st.button("🧹 RESET TOTAL DO QG"):
        db.execute("DELETE FROM modulos")
        db.commit()
        st.rerun()

# Painel de Controle dos Agentes
if agentes:
    st.subheader("⛽ Monitor de Tanque dos Agentes")
    cols = st.columns(4)
    for idx, ag in enumerate(agentes):
        with cols[idx % 4]:
            with st.container(border=True):
                try:
                    s_wei = w3.eth.get_balance(ag[2])
                    s_pol = round(w3.from_wei(s_wei, 'ether'), 3)
                except: s_pol = 0.0
                
                st.write(f"**{ag[1]}**")
                st.progress(min(s_pol / 0.5, 1.0))
                st.caption(f"Saldo: {s_pol} POL | Alvo: ${ag[5]}")
                
                if ag[9] == "VIGILANCIA":
                    auto_abastecer(ag[2])

    st.divider()
    st.subheader("🎯 Monitor de Mercado")
    preco_v = get_price(agentes[0][4])
    st.info(f"Cotação Atual {agentes[0][4]}: **${preco_v}**")
    
    # Lógica de Gatilho de Compra
    for ag in agentes:
        if ag[9] == "VIGILANCIA" and preco_v and preco_v <= ag[5]:
            db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao='COMPRADO' WHERE id=?", (preco_v, ag[0]))
            db.commit()
            st.rerun()

else:
    st.info("Aguardando ordem de lançamento na barra lateral.")

time.sleep(60)
st.rerun()