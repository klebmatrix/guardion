import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, os, secrets
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="GUARDION COMMANDER v5.0", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# --- BANCO DE DADOS (CÉREBRO DO EXÉRCITO) ---
def init_db():
    db_path = 'guardion_data.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    # Tenta criar ou atualizar a tabela
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    stop_loss REAL, status TEXT, ultima_acao TEXT, data_criacao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- FUNÇÕES DE APOIO ---
def get_live_price(coin):
    try:
        ids = {"WBTC": "bitcoin", "ETH": "ethereum", "POL": "matic-network"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        return requests.get(url, timeout=5).json()[ids[coin]]['usd']
    except: return None

def disparar_missil_gas(pk_mestre, valor_pol):
    acc_mestre = Account.from_key(pk_mestre)
    agentes = db.execute("SELECT endereco FROM modulos WHERE status != 'FINALIZADO'").fetchall()
    sucessos = 0
    for ag in agentes:
        try:
            nonce = w3.eth.get_transaction_count(acc_mestre.address)
            tx = {
                'nonce': nonce, 'to': ag[0], 'value': w3.to_wei(valor_pol, 'ether'),
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, pk_mestre)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            sucessos += 1
            time.sleep(0.3)
        except: pass
    return sucessos

# --- INTERFACE DE COMANDO ---
st.title("🎖️ QG GUARDION | COMANDO SUPREMO")

# Indicadores de Topo
agentes_ativos = db.execute("SELECT COUNT(*) FROM modulos WHERE status != 'FINALIZADO'").fetchone()[0]
c1, c2, c3 = st.columns(3)
c1.metric("Divisões Ativas", agentes_ativos)
c2.metric("Rede", "Polygon Mainnet", "ON")
c3.metric("Status Global", "Vigilância Total")

# --- SIDEBAR (FÁBRICA E LOGÍSTICA) ---
with st.sidebar:
    st.header("🏭 Fábrica de Batalhão")
    qtd = st.slider("Recrutar Agentes:", 1, 20, 5)
    moeda = st.selectbox("Alvo", ["WBTC", "ETH"])
    p_comp = st.number_input("Preço de Entrada (USD):", value=45000.0)
    
    if st.button("🚀 GERAR BATALHÃO"):
        for _ in range(qtd):
            acc = Account.create()
            db.execute("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, stop_loss, status, ultima_acao, data_criacao) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (f"AG-{secrets.token_hex(2).upper()}", acc.address, acc.key.hex(), moeda, p_comp, 0.0, 10.0, 5.0, "VIGILANCIA", "Pronto", datetime.now().strftime("%d/%m %H:%M")))
        db.commit()
        st.success(f"{qtd} Agentes Posicionados!")
        st.rerun()

    st.divider()
    st.header("🚀 Míssil de Gás")
    v_gas = st.number_input("POL por Agente:", value=0.5)
    pk_m = st.text_input("PK Mestre (Wallet 01):", type="password")
    if st.button("DISPARAR COMBUSTÍVEL"):
        if pk_m:
            num = disparar_missil_gas(pk_m, v_gas)
            st.success(f"Míssil entregue a {num} agentes!")
        else: st.error("Chave Mestre Necessária!")

# --- MONITOR DE GUERRA ---
tabs = st.tabs(["🎯 Vigilância", "🔥 Em Combate (Posicionados)", "📊 Histórico de Vitórias"])

# 

with tabs[0]: # VIGILÂNCIA
    vigi = db.execute("SELECT * FROM modulos WHERE status='VIGILANCIA'").fetchall()
    if vigi:
        for v in vigi:
            preco_v = get_live_price(v[4])
            with st.expander(f"🤖 {v[1]} - Alvo: {v[4]} (${v[5]})"):
                st.write(f"📍 Endereço: `{v[2]}`")
                st.write(f"💹 Preço Atual: **${preco_v}**")
                if preco_v and preco_v <= v[5]:
                    db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao=? WHERE id=?", (preco_v, "Compra Executada", v[0]))
                    db.commit()
                    st.rerun()
    else: st.info("Nenhum agente em vigilância.")

with tabs[1]: # POSICIONADO (TRADE ATIVO)
    pos = db.execute("SELECT * FROM modulos WHERE status='POSICIONADO'").fetchall()
    if pos:
        for p in pos:
            preco_p = get_live_price(p[4])
            alvo_v = p[6] * (1 + (p[7]/100))
            alvo_s = p[6] * (1 - (p[8]/100))
            with st.container(border=True):
                st.write(f"🚀 **{p[1]}** | Comprado a: **${p[6]}** | Atual: **${preco_p}**")
                st.progress(min(max((preco_p - alvo_s) / (alvo_v - alvo_s), 0.0), 1.0) if preco_p else 0.5)
                if preco_p and preco_p >= alvo_v:
                    db.execute("UPDATE modulos SET status='FINALIZADO', ultima_acao=? WHERE id=?", (f"Lucro em ${preco_p}", p[0]))
                    db.commit()
                    st.rerun()
                elif preco_p and preco_p <= alvo_s:
                    db.execute("UPDATE modulos SET status='STOPPED', ultima_acao=? WHERE id=?", (f"Stop em ${preco_p}", p[0]))
                    db.commit()
                    st.rerun()
    else: st.info("Nenhum agente em combate.")

with tabs[2]: # HISTÓRICO
    hist = pd.read_sql_query("SELECT nome, alvo, preco_compra, status, ultima_acao, data_criacao FROM modulos WHERE status IN ('FINALIZADO', 'STOPPED')", sqlite3.connect('guardion_data.db'))
    if not hist.empty:
        st.dataframe(hist, use_container_width=True)
        st.download_button("📥 Baixar Relatório", hist.to_csv(index=False), "relatorio.csv")
    else: st.write("Aguardando resultados...")

# Loop Automático
time.sleep(60)
st.rerun()