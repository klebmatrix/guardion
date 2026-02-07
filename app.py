import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, pandas as pd

# --- 1. CONFIGURAÇÃO E LOGIN ---
st.set_page_config(page_title="GUARDION OMNI v12.5", layout="wide")

# Senha mestra conforme sua instrução
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.5")
    senha_input = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha_input == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Chave Incorreta.")
    st.stop()

# --- 2. BANCO DE DADOS ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
db.commit()

# --- 3. MOTOR DE PREÇO RESILIENTE (ANTI-ERRO) ---
def pegar_preco():
    headers = {'User-Agent': 'Mozilla/5.0'}
    urls = [
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
        "https://api.kraken.com/0/public/Ticker?pair=XBTUSDT",
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    ]
    
    # Tentativa 1: Binance
    try:
        return float(requests.get(urls[0], timeout=3, headers=headers).json()['price'])
    except:
        # Tentativa 2: Kraken
        try:
            res = requests.get(urls[1], timeout=3).json()
            return float(res['result']['XXBTZUSD']['c'][0])
        except:
            # Tentativa 3: Pyth Network (Oráculo Direto)
            try:
                res = requests.get("https://hermes.pyth.network/v2/updates/price/latest?ids[]=0xe62df6c8b4a941d4072bf5c6bd4d13e8c1adb99517303f274483edc46271aee5", timeout=3).json()
                p = int(res['parsed'][0]['price']['price'])
                e = int(res['parsed'][0]['price']['expo'])
                return p * (10 ** e)
            except:
                return None

# --- 4. ENGINE DE TAKE PROFIT INFINITO ---
def processar_vendas_infinitas(btc_atual, meta_lucro_pct):
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    for ag in agentes:
        id_ag, nome, _, _, alvo, status, p_compra, _ = ag
        
        # Lógica de Compra
        if btc_atual <= alvo and status == "VIGILANCIA":
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultima_acao=? WHERE id=?", 
                       (btc_atual, f"Compra em ${btc_atual:,.2f}", id_ag))
            db.commit()
            st.toast(f"🎯 {nome} COMPROU!")

        # Lógica de Take Profit (RETRNO AO GRID INFINITO)
        elif status == "COMPRADO":
            meta = p_compra * (1 + (meta_lucro_pct / 100))
            if btc_atual >= meta:
                # Reset imediato para VIGILANCIA com o alvo original
                db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, ultima_acao=? WHERE id=?", 
                           (f"💰 Lucro Realizado! Resetado.", id_ag))
                db.commit()
                st.toast(f"💸 {nome} VENDEU COM LUCRO!")

# --- 5. INTERFACE DASHBOARD ---
st.title("🛡️ COMMANDER OMNI v12.5")
btc = pegar_preco()

if btc:
    st.success(f"SINAL ATIVO: BTC a ${btc:,.2f}")
    
    with st.sidebar:
        st.header("⚙️ AJUSTES DE COMBATE")
        if "pk_gas" not in st.session_state: st.session_state.pk_gas = ""
        st.session_state.pk_gas = st.text_input("Sua PK Mestra:", value=st.session_state.pk_gas, type="password")
        
        tp = st.slider("Take Profit (%)", 0.1, 10.0, 2.0)
        dist = st.number_input("Distância entre Snipers ($)", value=150)
        
        if st.button("🚀 LANÇAR 50 SNIPERS"):
            db.execute("DELETE FROM agentes_v6")
            for i in range(50):
                acc = Account.create()
                db.execute("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)",
                           (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), btc - (i * dist), "VIGILANCIA", 0.0, "Pronto"))
            db.commit()
            st.rerun()

    # Rodar Motor de Trade
    processar_vendas_infinitas(btc, tp)

    # Tabs de Monitoramento
    t1, t2 = st.tabs(["🎯 Radar de Preço", "📋 Log de Carteiras"])
    with t1:
        ags = db.execute("SELECT * FROM agentes_v6").fetchall()
        cols = st.columns(5)
        for i, a in enumerate(ags):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    if a[5] == "COMPRADO":
                        st.success(f"LUCRO: {((btc/a[6])-1)*100:.2f}%")
                    else:
                        st.info(f"Alvo: ${a[4]:,.0f}")
    with t2:
        df = pd.DataFrame(ags, columns=['ID', 'Nome', 'Endereço', 'Privada', 'Alvo', 'Status', 'Preço Compra', 'Última Ação'])
        st.dataframe(df[['Nome', 'Endereço', 'Status', 'Última Ação']], use_container_width=True)

else:
    st.error("⚠️ SEM SINAL DE REDE. Tentando reconectar...")
    time.sleep(5)
    st.rerun()

# Auto-Refresh
time.sleep(20)
st.rerun()