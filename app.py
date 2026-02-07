import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, os, secrets
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="GUARDION OMNI COMMANDER", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# --- SEGURANÇA (SECRETS) ---
PK_MESTRE = st.secrets.get("PK_MESTRE")

# --- BANCO DE DADOS (COM AUTO-CORREÇÃO) ---
def init_db():
    db_path = 'guardion_data.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    # Criar tabela base
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    stop_loss REAL, status TEXT, ultima_acao TEXT, data_criacao TEXT)''')
    # Garantir que colunas novas existam (Migração silenciosa)
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

def auto_abastecer(endereco_agente):
    """ Verifica se o agente precisa de combustível e envia da Wallet Mestre """
    if not PK_MESTRE: return
    try:
        acc_mestre = Account.from_key(PK_MESTRE)
        saldo_wei = w3.eth.get_balance(endereco_agente)
        limite_wei = w3.to_wei(0.1, 'ether')
        
        if saldo_wei < limite_wei:
            nonce = w3.eth.get_transaction_count(acc_mestre.address)
            tx = {
                'nonce': nonce, 'to': endereco_agente, 'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            st.toast(f"⛽ Míssil de Gás enviado para {endereco_agente[:6]}!", icon="🚀")
    except: pass

# --- INTERFACE DE COMANDO ---
st.title("🛡️ GUARDION OMNI | COMANDO AUTÔNOMO")

# Carregamento de dados inicial
cursor = db.cursor()
agentes = cursor.execute("SELECT * FROM modulos").fetchall()

# Métricas de Topo
c1, c2, c3, c4 = st.columns(4)
c1.metric("Exército Total", len(agentes))
c2.metric("Logística", "AUTOMÁTICA" if PK_MESTRE else "MANUAL")
c3.metric("Rede", "Polygon (POL)")
c4.metric("Ciclo", "60s")

# --- SIDEBAR: FÁBRICA DE AGENTES ---
with st.sidebar:
    st.header("🏭 Fábrica de Batalhão")
    qtd = st.slider("Quantidade:", 1, 10, 1)
    moeda_alvo = st.selectbox("Ativo", ["WBTC", "ETH"])
    p_gatilho = st.number_input("Preço de Entrada (USD):", value=45000.0)
    p_lucro = st.slider("Take Profit (%):", 2, 50, 10)
    p_stop = st.slider("Stop Loss (%):", 2, 30, 5)
    
    if st.button("🚀 RECRUTAR AGENTES"):
        for _ in range(qtd):
            acc = Account.create()
            db.execute("""INSERT INTO modulos 
                (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, stop_loss, status, ultima_acao, data_criacao) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (f"SNPR-{secrets.token_hex(2).upper()}", acc.address, acc.key.hex(), moeda_alvo, p_gatilho, 0.0, p_lucro, p_stop, "VIGILANCIA", "Pronto", datetime.now().strftime("%H:%M")))
        db.commit()
        st.rerun()

# --- PAINEL DE OPERAÇÕES ---
if agentes:
    t1, t2, t3 = st.tabs(["🎯 Vigilância", "🔥 Em Combate", "📊 Histórico"])

    with t1: # ABA VIGILÂNCIA
        vigi = [a for a in agentes if a[9] == "VIGILANCIA"]
        if vigi:
            for ag in vigi:
                id_m, nome, addr, priv, alvo, p_gat, p_com, luc, stp, status, acao, data = ag
                preco_agora = get_live_price(alvo)
                auto_abastecer(addr) # Tenta abastecer se estiver seco
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1,1,2])
                    col1.write(f"**{nome}**")
                    col1.caption(f"ID: `{addr[:8]}`")
                    col2.metric("Preço Atual", f"${preco_agora}")
                    col3.info(f"Aguardando queda para ${p_gat}")
                    
                    if preco_agora and preco_agora <= p_gat:
                        db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao=? WHERE id=?", (preco_agora, "Compra Executada", id_m))
                        db.commit()
                        st.rerun()
        else: st.info("Nenhum agente vigiando alvos no momento.")

    with t2: # ABA EM COMBATE (POSICIONADOS)
        pos = [a for a in agentes if a[9] == "POSICIONADO"]
        if pos:
            for ag in pos:
                id_m, nome, addr, priv, alvo, p_gat, p_comp, luc, stp, status, acao, data = ag
                preco_p = get_live_price(alvo)
                alvo_venda = p_comp * (1 + (luc/100))
                alvo_stop = p_comp * (1 - (stp/100))
                auto_abastecer(addr) # Garante gás para a venda
                
                with st.container(border=True):
                    st.write(f"🚀 **{nome}** em posição de **{alvo}**")
                    st.write(f"Preço Compra: ${p_comp} | Preço Atual: ${preco_p}")
                    
                    # Logica de Saída
                    if preco_p and preco_p >= alvo_venda:
                        db.execute("UPDATE modulos SET status='FINALIZADO', ultima_acao=? WHERE id=?", (f"Lucro: ${preco_p}", id_m))
                        db.commit()
                        st.rerun()
                    elif preco_p and preco_p <= alvo_stop:
                        db.execute("UPDATE modulos SET status='STOPPED', ultima_acao=? WHERE id=?", (f"Stop: ${preco_p}", id_m))
                        db.commit()
                        st.rerun()
        else: st.info("Nenhuma tropa em combate ativo.")

    with t3: # ABA HISTÓRICO
        df = pd.read_sql_query("SELECT nome, alvo, status, ultima_acao, data_criacao FROM modulos WHERE status IN ('FINALIZADO', 'STOPPED')", sqlite3.connect('guardion_data.db'))
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Exportar Relatório", df.to_csv(index=False), "performance.csv")
        else: st.write("Aguardando primeiras vitórias.")

else:
    st.info("O seu exército está vazio. Recrute agentes na barra lateral para começar.")

# --- AUTO REFRESH ---
time.sleep(60)
st.rerun()