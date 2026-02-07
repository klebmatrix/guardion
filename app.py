import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, secrets, requests

st.set_page_config(page_title="GUARDION SENTINEL", layout="wide")

# Conexão RPC (Polygon)
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# --- BANCO DE DATOS ---
def init_db():
    conn = sqlite3.connect('guardion_data.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_alvo REAL, status TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- FUNÇÃO DE PREÇO REAL (via CoinGecko) ---
def buscar_preco(ticker):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ticker}&vs_currencies=usd"
        res = requests.get(url).json()
        return res[ticker]['usd']
    except: return 0.0

# --- LÓGICA DO SENTINELA (Decisão do Robô) ---
def monitorar_e_executar(modulo):
    preco_atual = buscar_preco("bitcoin" if modulo['alvo'] == "WBTC" else "ethereum")
    
    if preco_atual <= modulo['preco_alvo'] and modulo['status'] == "AGUARDANDO":
        # Aqui o bot decide agir sozinho
        st.toast(f"🚨 GATILHO DISPARADO: {modulo['nome']} comprando {modulo['alvo']}!")
        # [A lógica de swap real entra aqui usando modulo['privada']]
        return True
    return False

# --- INTERFACE PRINCIPAL ---
st.title("🛡️ MODO SENTINELA ATIVO")

# Criar Módulo Autônomo
with st.sidebar:
    st.header("⚙️ Configurar Agente")
    alvo = st.selectbox("Moeda Alvo", ["WBTC", "ETH"])
    p_alvo = st.number_input("Comprar quando o preço for menor que:", value=40000.0)
    
    if st.button("ATIVAR NOVO AGENTE"):
        priv = "0x" + secrets.token_hex(32)
        acc = Account.from_key(priv)
        conn.execute("INSERT INTO modulos (nome, endereco, privada, alvo, preco_alvo, status) VALUES (?,?,?,?,?,?)",
                     (f"SENTINEL-{alvo}", acc.address, priv, alvo, p_alvo, "AGUARDANDO"))
        conn.commit()
        st.success("Agente em Vigilância!")

# Painel de Monitoramento
st.subheader("📡 Vigilância em Tempo Real")
modulos = conn.execute("SELECT * FROM modulos").fetchall()



if modulos:
    for m in modulos:
        m_dict = {"id":m[0], "nome":m[1], "endereco":m[2], "privada":m[3], "alvo":m[4], "preco_alvo":m[5], "status":m[6]}
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"**{m_dict['nome']}**")
            c2.metric("Alvo de Compra", f"${m_dict['preco_alvo']}")
            
            # Simulação de verificação constante
            if monitorar_e_executar(m_dict):
                st.success(f"ORDEM EXECUTADA PARA {m_dict['nome']}")
            else:
                c3.write("🔍 Monitorando...")
                c4.write(f"📍 Carteira: `{m_dict['endereco'][:6]}...`")

# Auto-refresh para o bot não dormir
st.info("O bot verifica os preços automaticamente a cada 60 segundos.")
time.sleep(60)
st.rerun()