import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, os, secrets
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="GUARDION GRID COMMANDER", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# --- SEGURANÇA (DADOS DOS SECRETS) ---
PK_MESTRE = st.secrets.get("PK_MESTRE")

# --- BANCO DE DADOS (COM AUTO-MIGRAÇÃO) ---
def init_db():
    conn = sqlite3.connect('guardion_data.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    stop_loss REAL, status TEXT, ultima_acao TEXT, data_criacao TEXT)''')
    try: conn.execute("ALTER TABLE modulos ADD COLUMN data_criacao TEXT")
    except: pass
    conn.commit()
    return conn

db = init_db()

# --- FUNÇÕES DE INTELIGÊNCIA ---
def get_live_price(coin):
    try:
        ids = {"WBTC": "bitcoin", "ETH": "ethereum", "POL": "matic-network"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        return requests.get(url, timeout=5).json()[ids[coin]]['usd']
    except: return None

def auto_abastecer(addr):
    """ O Míssil Inteligente: Abastece o agente se o POL estiver acabando """
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
            st.toast(f"⛽ Reabastecido: {addr[:6]}", icon="🚀")
    except: pass

# --- INTERFACE ---
st.title("🎖️ QG GUARDION | GRID STRATEGY")

# Dados do Exército
cursor = db.cursor()
agentes = cursor.execute("SELECT * FROM modulos").fetchall()

# Métricas
m1, m2, m3 = st.columns(3)
m1.metric("Batalhões Ativos", len([a for a in agentes if a[9] != 'FINALIZADO']))
m2.metric("Logística", "AUTÔNOMA" if PK_MESTRE else "MANUAL")
m3.metric("Rede", "Polygon (POL)")

# --- SIDEBAR: FÁBRICA DE GRID ---
with st.sidebar:
    st.header("🏭 Fábrica de Grid Escalonado")
    
    qtd = st.select_slider("Quantidade de Agentes:", options=[1, 5, 10, 25, 50, 100], value=25)
    moeda_alvo = st.selectbox("Ativo", ["WBTC", "ETH"])
    
    st.divider()
    p_topo = st.number_input("Preço Inicial (Topo):", value=45000.0)
    distancia = st.number_input("Distância entre Agentes ($):", value=100.0)
    
    p_final = p_topo - (qtd * distancia)
    st.info(f"📍 Rede cobrirá de ${p_topo} até ${p_final}")

    if st.button(f"🚀 LANÇAR REDE DE {qtd} AGENTES"):
        with st.status("Preparando agentes...", expanded=False) as status:
            novos = []
            for i in range(qtd):
                acc = Account.create()
                p_ajustado = p_topo - (i * distancia)
                novos.append((f"GRID-{i+1:02d}", acc.address, acc.key.hex(), moeda_alvo, 
                             p_ajustado, 0.0, 10.0, 5.0, "VIGILANCIA", f"Alvo: ${p_ajustado}", 
                             datetime.now().strftime("%H:%M")))
            
            db.cursor().executemany("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, stop_loss, status, ultima_acao, data_criacao) VALUES (?,?,?,?,?,?,?,?,?,?,?)", novos)
            db.commit()
            status.update(label="✅ Rede Posicionada!", state="complete")
        st.rerun()

    st.divider()
    if st.button("🧹 LIMPAR MORTOS (FINALIZADOS)"):
        db.execute("DELETE FROM modulos WHERE status IN ('FINALIZADO', 'STOPPED')")
        db.commit()
        st.rerun()

# --- PAINEL DE COMANDO ---
if agentes:
    t1, t2, t3 = st.tabs(["🎯 Alvos do Grid", "🔥 Em Combate", "📊 Histórico"])

    with t1:
        vigi = [a for a in agentes if a[9] == "VIGILANCIA"]
        if vigi:
            preco_v = get_live_price(vigi[0][4])
            st.write(f"💹 Preço Atual {vigi[0][4]}: **${preco_v}**")
            
            # Gráfico de Escalonamento (Simplificado)
            grid_data = pd.DataFrame([{"Nome": a[1], "Preço Alvo": a[5]} for a in vigi])
            st.bar_chart(grid_data.set_index("Nome"))

            for ag in vigi:
                auto_abastecer(ag[2])
                if preco_v and preco_v <= ag[5]:
                    db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao=? WHERE id=?", (preco_v, "Compra!", ag[0]))
                    db.commit()
                    st.rerun()
        else: st.info("Nenhuma rede ativa.")

    with t2:
        pos = [a for a in agentes if a[9] == "POSICIONADO"]
        for ag in pos:
            auto_abastecer(ag[2])
            st.warning(f"🚀 {ag[1]} - Comprado em ${ag[6]}. Aguardando lucro.")

    with t3:
        hist = pd.read_sql_query("SELECT nome, alvo, status, ultima_acao FROM modulos WHERE status != 'VIGILANCIA'", sqlite3.connect('guardion_data.db'))
        st.dataframe(hist, use_container_width=True)

else:
    st.info("QG pronto. Configure sua rede na lateral.")

time.sleep(60)
st.rerun()