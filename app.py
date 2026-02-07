import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, secrets, requests, os
from datetime import datetime

# 1. Configuração e Conexão
st.set_page_config(page_title="SENTINEL OMNI PRO", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# 2. Banco de Dados Evoluído (Com Preço de Compra e Alvo de Venda)
def init_db():
    db_path = 'guardion_data.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        conn.execute("SELECT preco_compra FROM modulos LIMIT 1")
    except:
        conn.close()
        if os.path.exists(db_path): os.remove(db_path)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute('''CREATE TABLE modulos 
                        (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                        alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                        status TEXT, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

def get_live_price(coin):
    try:
        ids = {"WBTC": "bitcoin", "ETH": "ethereum", "POL": "matic-network"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        return requests.get(url, timeout=5).json()[ids[coin]]['usd']
    except: return None

# --- INTERFACE ---
st.title("🛡️ GUARDION SENTINEL | CICLO DE LUCRO")

with st.sidebar:
    st.header("⚡ Novo Agente de Ciclo")
    moeda = st.selectbox("Moeda", ["WBTC", "ETH"])
    p_compra = st.number_input("Comprar em (USD):", value=40000.0)
    p_lucro = st.slider("Vender com lucro de (%):", 2, 50, 10)
    
    if st.button("ATIVAR CICLO COMPLETO"):
        acc = Account.create() 
        db.execute("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, status, ultima_acao) VALUES (?,?,?,?,?,?,?,?,?)",
                   (f"TRADER-{moeda}", acc.address, acc.key.hex(), moeda, p_compra, 0.0, p_lucro, "VIGILANCIA", "Aguardando Queda"))
        db.commit()
        st.success("Agente em campo!")

# 3. Lógica do Sentinela: Compra e Venda
agentes = db.execute("SELECT * FROM modulos").fetchall()



if agentes:
    for ag in agentes:
        id_m, nome, addr, priv, alvo, p_gatilho, p_comprado, lucro_pct, status, u_acao = ag
        preco_agora = get_live_price(alvo)
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            c1.write(f"**{nome}**\n`{addr[:8]}...`")
            c2.metric(f"{alvo} Atual", f"${preco_agora}")
            
            # ESTADO 1: Aguardando para Comprar
            if status == "VIGILANCIA":
                c3.metric("Alvo de Compra", f"${p_gatilho}")
                if preco_agora and preco_agora <= p_gatilho:
                    db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao=? WHERE id=?", 
                               (preco_agora, f"Comprou a ${preco_agora}", id_m))
                    db.commit()
                    st.rerun()
                c4.info("🔍 Monitorando preço para entrada...")

            # ESTADO 2: Comprado, aguardando lucro para vender
            elif status == "POSICIONADO":
                alvo_venda = p_comprado * (1 + (lucro_pct / 100))
                c3.metric("Alvo de Venda", f"${alvo_venda:.2f}", delta=f"{lucro_pct}%")
                
                if preco_agora and preco_agora >= alvo_venda:
                    db.execute("UPDATE modulos SET status='FINALIZADO', ultima_acao=? WHERE id=?", 
                               (f"Vendeu a ${preco_agora} (Lucro!)", id_m))
                    db.commit()
                    st.rerun()
                c4.warning("📈 Posicionado! Aguardando valorização...")

            elif status == "FINALIZADO":
                c3.write("✅ Operação Concluída")
                c4.success(f"Resultado: {u_acao}")

# 4. Auto-Refresh
time.sleep(60)
st.rerun()