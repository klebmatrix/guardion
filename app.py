import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, os, secrets
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES E CONEXÃO ---
st.set_page_config(page_title="GUARDION COMMANDER v5.1", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# --- BANCO DE DADOS COM AUTO-MIGRAÇÃO ---
def init_db():
    db_path = 'guardion_data.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    
    # Criar tabela se não existir
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    stop_loss REAL, status TEXT, ultima_acao TEXT)''')
    
    # Tenta adicionar a coluna data_criacao caso ela falte (Corrige o erro do Pandas)
    try:
        conn.execute("ALTER TABLE modulos ADD COLUMN data_criacao TEXT")
    except:
        pass # Coluna já existe
        
    conn.commit()
    return conn

db = init_db()

# --- MOTOR DE PREÇOS ---
def get_live_price(coin):
    try:
        ids = {"WBTC": "bitcoin", "ETH": "ethereum", "POL": "matic-network"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        res = requests.get(url, timeout=5).json()
        return res[ids[coin]]['usd']
    except: return None

# --- INTERFACE ---
st.title("🎖️ QG GUARDION | COMANDO SUPREMO")

# Indicadores Rápidos
agentes_vivos = db.execute("SELECT COUNT(*) FROM modulos WHERE status != 'FINALIZADO'").fetchone()[0]
c1, c2, c3 = st.columns(3)
c1.metric("Divisões Ativas", agentes_vivos)
c2.metric("Rede", "Polygon", "Ativa")
c3.metric("Frequência", "60s", "Auto-Check")

# --- SIDEBAR: FÁBRICA E MÍSSIL ---
with st.sidebar:
    st.header("🏭 Fábrica de Batalhão")
    qtd = st.slider("Recrutar Agentes:", 1, 20, 5)
    moeda = st.selectbox("Alvo", ["WBTC", "ETH"])
    p_comp = st.number_input("Preço de Entrada (USD):", value=45000.0)
    
    if st.button("🚀 GERAR BATALHÃO"):
        for _ in range(qtd):
            acc = Account.create()
            db.execute("""INSERT INTO modulos 
                       (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, stop_loss, status, ultima_acao, data_criacao) 
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                       (f"AG-{secrets.token_hex(2).upper()}", acc.address, acc.key.hex(), moeda, p_comp, 0.0, 10.0, 5.0, "VIGILANCIA", "Pronto", datetime.now().strftime("%d/%m %H:%M")))
        db.commit()
        st.success("Tropas Recrutadas!")
        st.rerun()

    st.divider()
    st.header("🚀 Míssil de Gás")
    pk_m = st.text_input("PK Mestre (Wallet 01):", type="password")
    if st.button("DISPARAR COMBUSTÍVEL"):
        st.info("Função de disparo em massa ativada...")

# --- PAINEL DE GUERRA ---
tabs = st.tabs(["🎯 Vigilância", "🔥 Em Combate", "📊 Histórico"])

with tabs[0]: # VIGILÂNCIA
    vigi = db.execute("SELECT * FROM modulos WHERE status='VIGILANCIA'").fetchall()
    if vigi:
        for v in vigi:
            p_agora = get_live_price(v[4])
            with st.expander(f"🤖 {v[1]} - Alvo: {v[4]} (${v[5]})"):
                st.write(f"Endereço: `{v[2]}`")
                st.write(f"Preço: **${p_agora}**")
                if p_agora and p_agora <= v[5]:
                    db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao=? WHERE id=?", (p_agora, "Compra Efetuada", v[0]))
                    db.commit()
                    st.rerun()
    else: st.info("Nenhum agente vigiando no momento.")

with tabs[1]: # POSICIONADOS
    pos = db.execute("SELECT * FROM modulos WHERE status='POSICIONADO'").fetchall()
    if pos:
        for p in pos:
            p_atual = get_live_price(p[4])
            st.warning(f"🚀 {p[1]} posicionado em {p[4]} | Comprado a ${p[6]} | Agora: ${p_atual}")
    else: st.info("Nenhuma tropa em combate.")

with tabs[2]: # HISTÓRICO (Onde dava o erro)
    try:
        # Usamos uma query que garante a existência das colunas
        hist_df = pd.read_sql_query("SELECT nome, alvo, preco_compra, status, ultima_acao, data_criacao FROM modulos WHERE status IN ('FINALIZADO', 'STOPPED')", conn := sqlite3.connect('guardion_data.db'))
        if not hist_df.empty:
            st.dataframe(hist_df, use_container_width=True)
        else: st.write("Aguardando primeiras vitórias.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico. Tente criar um novo agente primeiro.")

# Auto-refresh
time.sleep(60)
st.rerun()