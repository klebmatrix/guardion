import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- CONFIGURAÇÃO DE REDE ---
st.set_page_config(page_title="GUARDION OMNI v11.2", layout="wide")
RPC_URL = "https://polygon-rpc.com" 
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- BANCO DE DADOS (V4 - ESTRUTURA COMPLETA) ---
def init_db():
    conn = sqlite3.connect('guardion_v4.db', check_same_thread=False)
    # Criando a tabela V4 com todas as colunas necessárias para evitar o erro de inserção
    conn.execute('''CREATE TABLE IF NOT EXISTS agentes_v4 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- INTERFACE LATERAL ---
with st.sidebar:
    st.header("🔐 ACESSO MESTRE")
    pk_input = st.text_input("Sua PK_01 Conectada:", type="password", key="pk_main")
    
    PK_MESTRE = None
    if pk_input:
        try:
            pk_limpa = pk_input.strip().replace('"', '').replace("'", "")
            if not pk_limpa.startswith("0x") and len(pk_limpa) == 64: pk_limpa = "0x" + pk_limpa
            acc_mestre = Account.from_key(pk_limpa)
            PK_MESTRE = pk_limpa
            st.success("✅ MESTRE ONLINE")
        except: st.error("❌ Chave Inválida")

    st.divider()
    st.header("⚙️ AJUSTES")
    p_topo = st.number_input("Preço Inicial (BTC):", value=102500.0)
    distancia = st.number_input("Distância Grid ($):", value=200.0)
    lucro_desejado = st.number_input("Lucro para Venda ($):", value=500.0)
    
    if st.button("🚀 REINICIAR BATALHÃO (25)"):
        if not PK_MESTRE: 
            st.warning("Conecte a PK primeiro!")
        else:
            # Limpa apenas a tabela v4
            db.execute("DELETE FROM agentes_v4")
            novos = []
            for i in range(25):
                acc = Account.create()
                alvo = p_topo - (i * distancia)
                # 7 valores para 7 colunas (id é automático)
                novos.append((f"SNIPER-{i+1:02d}", acc.address, acc.key.hex(), alvo, "VIGILANCIA", 0.0, "Aguardando"))
            
            db.executemany("INSERT INTO agentes_v4 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)", novos)
            db.commit()
            st.rerun()

# --- MONITOR DE PREÇO ---
def get_btc_price():
    try: 
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        return float(res.json()['price'])
    except: return 0.0

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v11.2")
btc_atual = get_btc_price()

st.metric("BTC ATUAL", f"${btc_atual:,.2f}")
st.divider()

# Listagem usando a tabela v4
agentes = db.execute("SELECT * FROM agentes_v4").fetchall()
if agentes:
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        # Mapeamento: 0:id, 1:nome, 2:endereco, 3:privada, 4:alvo, 5:status, 6:preco_compra, 7:ultima_acao
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                st.caption(f"Status: {ag[5]}")
                st.write(f"🎯 Alvo: ${ag[4]:,.0f}")
                if ag[5] == "COMPRADO":
                    st.success(f"Comprou: ${ag[6]:,.0f}")
else:
    st.info("Aguardando criação dos agentes v4...")

time.sleep(45)
st.rerun()