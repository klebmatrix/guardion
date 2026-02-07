import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v12.6", layout="wide")
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.6")
    senha = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
    st.stop()

db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

# --- MOTOR DE PREÇO BLINDADO ---
def pegar_preco():
    # Simulando um navegador real para evitar bloqueios
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # Lista de endpoints em ordem de confiança
    tentativas = [
        lambda: float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5, headers=headers).json()['price']),
        lambda: float(requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDT", timeout=5).json()['result']['XXBTZUSD']['c'][0]),
        lambda: float(requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5).json()['bitcoin']['usd']),
        lambda: float(requests.get("https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD", timeout=5).json()['USD'])
    ]

    for func in tentativas:
        try:
            return func()
        except:
            continue
    return None

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v12.6")

# Tenta pegar o preço
btc = pegar_preco()

# Se falhar, permite entrada manual para não travar o sistema
if not btc:
    st.warning("⚠️ Falha em todas as APIs. Verifique sua internet ou VPN.")
    btc_manual = st.number_input("Insira o preço do BTC manualmente para rodar os Snipers:", value=0.0)
    if btc_manual > 0:
        btc = btc_manual

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}", delta="SINAL ATIVO")
    
    with st.sidebar:
        st.header("⚙️ CONFIGURAÇÕES")
        tp = st.slider("Take Profit (%)", 0.1, 5.0, 1.5)
        if st.button("🚀 REINICIAR GRID"):
            # Lógica de reset (apaga e cria 50 novos)
            db.execute("DELETE FROM agentes_v6")
            for i in range(50):
                acc = Account.create()
                db.execute("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)",
                           (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), btc - (i * 150), "VIGILANCIA", 0.0, "Pronto"))
            db.commit()
            st.rerun()

    # MOTOR DE TRADE (ATIVO INFINITO)
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    for ag in agentes:
        id_ag, nome, _, _, alvo, status, p_compra, _ = ag
        # Compra
        if btc <= alvo and status == "VIGILANCIA":
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultima_acao='Comprou' WHERE id=?", (btc, id_ag))
            db.commit()
        # Venda Infinita
        elif status == "COMPRADO" and btc >= p_compra * (1 + (tp/100)):
            db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, ultima_acao='Lucro/Reset' WHERE id=?", (id_ag,))
            db.commit()

    # Exibição
    cols = st.columns(5)
    for i, ag in enumerate(agentes):
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                st.caption(ag[5])

else:
    st.error("ERRO CRÍTICO: Sem conexão com a rede e sem preço manual.")

time.sleep(15)
st.rerun()