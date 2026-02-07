import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3
import time
import requests
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="GUARDION OMNI v12.5", layout="wide", page_icon="🛡️")

# --- 2. SISTEMA DE LOGIN (SEGURANÇA TOTAL) ---
if "logado" not in st.session_state:
    st.session_state.logado = False

def tela_login():
    st.title("🔐 QG COMMANDER OMNI")
    # Tenta ler a SECRET_KEY dos Secrets do Streamlit, senão usa o padrão
    senha_mestre = st.secrets.get("SECRET_KEY", "mestre2026")
    
    with st.container(border=True):
        senha_input = st.text_input("Chave de Acesso ao Batalhão:", type="password")
        if st.button("DESBLOQUEAR SISTEMA"):
            if senha_input == senha_mestre:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("❌ Chave incorreta. Acesso negado.")
    st.stop()

if not st.session_state.logado:
    tela_login()

# --- 3. BANCO DE DADOS (v7 - AGENTES E LOGS) ---
def init_db():
    conn = sqlite3.connect('guardion_v7.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS agentes_v7 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT, data_hora TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- 4. MOTOR DE PREÇO (MULTI-FONTE) ---
def get_live_price():
    # Tenta Binance -> Kraken -> Coinbase
    try:
        return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()['price'])
    except:
        try:
            return float(requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDT").json()['result']['XBTUSDT']['c'][0])
        except:
            return None

# --- 5. LÓGICA DE EXECUÇÃO (O CÉREBRO) ---
def processar_estrategia(btc_preco):
    agentes = db.execute("SELECT * FROM agentes_v7").fetchall()
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, acao, data = ag
        agora = datetime.now().strftime("%d/%m %H:%M:%S")
        
        # Lógica de Compra
        if status == "VIGILANCIA" and btc_preco <= alvo:
            db.execute("UPDATE agentes_v7 SET status='COMPRADO', preco_compra=?, ultima_acao='COMPRA EXECUTADA', data_hora=? WHERE id=?", (btc_preco, agora, id_b))
            db.commit()
            
        # Lógica de Venda (Lucro de $500 padrão ou ajuste aqui)
        elif status == "COMPRADO" and btc_preco >= (p_compra + 500):
            db.execute("UPDATE agentes_v7 SET status='VIGILANCIA', preco_compra=0, ultima_acao='LUCRO NO BOLSO', data_hora=? WHERE id=?", (agora, id_b))
            db.commit()

# --- 6. INTERFACE DE COMANDO ---
st.title("🛡️ COMMANDER OMNI | SISTEMA AUTÔNOMO v12.5")

btc_atual = get_live_price()
if btc_atual:
    st.metric("PREÇO BTC/USDT", f"${btc_atual:,.2f}", delta_color="normal")
    processar_estrategia(btc_atual)
else:
    st.warning("⚠️ Aguardando conexão com servidores de preço...")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ COMANDO CENTRAL")
    if st.button("🚪 ENCERRAR SESSÃO"):
        st.session_state.logado = False
        st.rerun()
    
    st.divider()
    pk_mestre = st.text_input("Sua PK_01 (Mestre):", type="password", help="Chave para abastecer POL")
    topo_grid = st.number_input("Preço Inicial do Grid ($):", value=btc_atual if btc_atual else 100000.0)
    espacamento = st.number_input("Espaçamento entre Snipers ($):", value=150)

    if st.button("🚀 LANÇAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes_v7")
        novos_agentes = []
        for i in range(50):
            acc = Account.create()
            alvo_calc = topo_grid - (i * espacamento)
            novos_agentes.append((
                f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), 
                alvo_calc, "VIGILANCIA", 0.0, "POSICIONADO", datetime.now().strftime("%H:%M:%S")
            ))
        db.executemany("INSERT INTO agentes_v7 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao, data_hora) VALUES (?,?,?,?,?,?,?,?)", novos_agentes)
        db.commit()
        st.success("🎯 Batalhão de 50 Agentes em campo!")
        st.rerun()

# --- 7. PAINEL DE MONITORAMENTO ---
tab_monitor, tab_logs = st.tabs(["🎯 GRID DE VIGILÂNCIA", "📊 RELATÓRIO DE OPERAÇÕES"])

with tab_monitor:
    agentes = db.execute("SELECT * FROM agentes_v7").fetchall()
    if agentes:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes):
            with cols[idx % 5]:
                with st.container(border=True):
                    cor_status = "🟢" if ag[5] == "COMPRADO" else "🔵"
                    st.write(f"{cor_status} **{ag[1]}**")
                    st.caption(f"🎯 Alvo: ${ag[4]:,.0f}")
                    if ag[5] == "COMPRADO":
                        st.write(f"💰 In: ${ag[6]:,.0f}")
                    else:
                        st.write("🔭 Vigilante")
    else:
        st.info("O batalhão está no quartel. Use o comando lateral para lançar os 50 snipers.")

with tab_logs:
    st.subheader("📑 Histórico de Movimentação em Tempo Real")
    if agentes:
        import pandas as pd
        # Mostra apenas as colunas relevantes para o relatório
        df = pd.DataFrame(agentes, columns=['ID', 'Nome', 'Carteira', 'PK', 'Alvo', 'Status', 'Preço Compra', 'Mensagem', 'Última Atualização'])
        st.dataframe(df[['Nome', 'Status', 'Alvo', 'Preço Compra', 'Mensagem', 'Última Atualização']], use_container_width=True)
    else:
        st.write("Sem registros no momento.")

# --- 8. CICLO DE VIDA (AUTONOMIA) ---
st.caption(f"Última varredura do servidor: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(15) # Atualiza a cada 15 segundos
st.rerun()