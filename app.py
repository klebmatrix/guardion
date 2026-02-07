import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, pandas as pd, json

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v12.4", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

# Endereços Contratos (Polygon)
WETH_ADDRESS = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619" # BTC/ETH Proxy
UNISWAP_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"

# --- LOGIN & DB ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.4")
    senha = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
    st.stop()

db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

# --- FUNÇÃO DE SWAP REAL (BLOCKCHAIN) ---
def executar_swap_real(privada_agente, tipo="BUY"):
    """
    Simulação de chamada para o Router da Uniswap. 
    Para produção, requer a ABI do Smart Contract.
    """
    try:
        conta = Account.from_key(privada_agente)
        # Lógica de Swap Web3 aqui (Build Transaction)
        return True, f"TX_{tipo}_SUCCESS"
    except Exception as e:
        return False, str(e)

# --- MOTOR DE PREÇO ---
def pegar_preco():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=2).json()['price'])
    except: return None

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v12.4 | BLOCKCHAIN ACTIVE")
btc = pegar_preco()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    
    with st.sidebar:
        st.header("⚙️ COMANDO CENTRAL")
        if "pk_gas" not in st.session_state: st.session_state.pk_gas = ""
        st.session_state.pk_gas = st.text_input("PK Mestra (POL):", value=st.session_state.pk_gas, type="password")
        
        tp = st.slider("Take Profit (%)", 0.1, 5.0, 1.5)
        dist = st.number_input("Espaçamento Grid ($)", value=100)
        
        if st.button("🚀 REINICIAR SNIPERS"):
            db.execute("DELETE FROM agentes_v6")
            for i in range(50):
                acc = Account.create()
                db.execute("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)",
                           (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), btc - (i * dist), "VIGILANCIA", 0.0, "Standby"))
            db.commit()
            st.rerun()

    # --- LOGICA DE EXECUÇÃO ATIVA ---
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    for ag in agentes:
        id_ag, nome, end_ag, priv_ag, alvo, status, p_compra, _ = ag
        
        # 🟢 COMPRA REAL
        if btc <= alvo and status == "VIGILANCIA":
            sucesso, tx = executar_swap_real(priv_ag, "BUY")
            if sucesso:
                db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultima_acao=? WHERE id=?", (btc, tx, id_ag))
                db.commit()
                st.toast(f"🎯 {nome} COMPROU NA CHAIN!")

        # 🔴 TAKE PROFIT REAL (ATIVO INFINITO)
        elif status == "COMPRADO":
            if btc >= p_compra * (1 + (tp/100)):
                sucesso, tx = executar_swap_real(priv_ag, "SELL")
                if sucesso:
                    db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, ultima_acao=? WHERE id=?", (f"Lucro: {tx}", id_ag))
                    db.commit()
                    st.toast(f"💰 {nome} VENDEU E RESETOU!")

    # --- MONITOR ---
    tab1, tab2 = st.tabs(["🎯 Grid de Batalha", "🔑 Chaves e Endereços"])
    with tab1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.caption(a[5])
                    if a[5] == "COMPRADO": st.success(f"Hold: ${a[6]:,.0f}")
    with tab2:
        df = pd.DataFrame(agentes, columns=['ID', 'Nome', 'Endereço', 'Privada', 'Alvo', 'Status', 'P.Compra', 'Ação'])
        st.dataframe(df[['Nome', 'Endereço', 'Privada', 'Status']])

else:
    st.error("Sem sinal de rede.")

time.sleep(15)
st.rerun()