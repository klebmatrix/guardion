import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, secrets, requests, os
from datetime import datetime

# 1. Configuração e Conexão
st.set_page_config(page_title="SENTINEL RISK PRO", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# 2. Banco de Dados com Stop Loss
def init_db():
    db_path = 'guardion_data.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        conn.execute("SELECT stop_loss FROM modulos LIMIT 1")
    except:
        conn.close()
        if os.path.exists(db_path): os.remove(db_path)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute('''CREATE TABLE modulos 
                        (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                        alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                        stop_loss REAL, status TEXT, ultima_acao TEXT)''')
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
st.title("🛡️ GUARDION SENTINEL | RISK MANAGEMENT")

with st.sidebar:
    st.header("⚡ Configurar Estratégia")
    moeda = st.selectbox("Ativo", ["WBTC", "ETH"])
    p_compra = st.number_input("Comprar em (USD):", value=40000.0)
    p_lucro = st.slider("Take Profit (Vender no Lucro %):", 2, 100, 10)
    p_stop = st.slider("Stop Loss (Vender na Queda %):", 2, 50, 5)
    
    if st.button("ATIVAR AGENTE COM STOP LOSS"):
        acc = Account.create() 
        db.execute("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, stop_loss, status, ultima_acao) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (f"SENTINEL-{moeda}", acc.address, acc.key.hex(), moeda, p_compra, 0.0, p_lucro, p_stop, "VIGILANCIA", "Aguardando Entrada"))
        db.commit()
        st.success("Agente com Gestão de Risco Ativado!")

# 3. Lógica de Operação
agentes = db.execute("SELECT * FROM modulos").fetchall()



if agentes:
    for ag in agentes:
        id_m, nome, addr, priv, alvo, p_gatilho, p_comprado, lucro_pct, stop_pct, status, u_acao = ag
        preco_agora = get_live_price(alvo)
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            c1.write(f"**{nome}**\n`{addr[:8]}...`")
            c2.metric(f"{alvo} Atual", f"${preco_agora}")
            
            # --- LÓGICA DE COMPRA ---
            if status == "VIGILANCIA":
                c3.metric("Alvo Compra", f"${p_gatilho}")
                if preco_agora and preco_agora <= p_gatilho:
                    db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao=? WHERE id=?", 
                               (preco_agora, f"Comprou a ${preco_agora}", id_m))
                    db.commit()
                    st.rerun()
                c4.info("🔍 Monitorando entrada...")

            # --- LÓGICA DE SAÍDA (LUCRO OU PREJUÍZO) ---
            elif status == "POSICIONADO":
                alvo_venda = p_comprado * (1 + (lucro_pct / 100))
                alvo_stop = p_comprado * (1 - (stop_pct / 100))
                
                c3.metric("Meta Lucro", f"${alvo_venda:.1f}")
                c3.metric("Stop Loss", f"${alvo_stop:.1f}", delta=f"-{stop_pct}%", delta_color="inverse")
                
                # Checar Venda no Lucro
                if preco_agora and preco_agora >= alvo_venda:
                    db.execute("UPDATE modulos SET status='FINALIZADO', ultima_acao=? WHERE id=?", 
                               (f"LUCRO: Vendeu a ${preco_agora}", id_m))
                    db.commit()
                    st.rerun()
                
                # Checar Stop Loss (Venda na Queda)
                elif preco_agora and preco_agora <= alvo_stop:
                    db.execute("UPDATE modulos SET status='STOPPED', ultima_acao=? WHERE id=?", 
                               (f"STOP: Protegeu em ${preco_agora}", id_m))
                    db.commit()
                    st.rerun()
                
                c4.warning("📈 Em posição... Monitorando alvos.")

            elif status in ["FINALIZADO", "STOPPED"]:
                c3.write("🏁 Operação Encerrada")
                c4.success(f"Resultado Final: {u_acao}")

# 4. Loop de Atualização
time.sleep(60)
st.rerun()