import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v12.9", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"
EXPLORER_URL = "https://polygonscan.com/tx/"

# --- LOGIN SEGURO ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.9")
    senha = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- DB & ESTRUTURA ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)
try: db.execute("ALTER TABLE agentes_v6 ADD COLUMN last_hash TEXT")
except: pass
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT, last_hash TEXT)''')
db.commit()

# --- MOTOR DE PREÇO (COM BYPASS DE ERRO) ---
def pegar_preco():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Tenta Binance
        return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3, headers=headers).json()['price'])
    except:
        try:
            # Tenta CoinGecko (Backup)
            return float(requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()['bitcoin']['usd'])
        except:
            return None

# --- LOGÍSTICA DE GÁS (DIVIDIR POL) ---
def dividir_pol(pk_mestra, valor):
    w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
    if not w3.is_connected():
        st.error("Erro ao conectar na rede Polygon!")
        return
    
    mestra = Account.from_key(pk_mestra)
    agentes = db.execute("SELECT endereco FROM agentes_v6").fetchall()
    st.warning(f"🚀 Enviando {valor} POL para {len(agentes)} snipers...")
    
    progresso = st.progress(0)
    for i, (end,) in enumerate(agentes):
        try:
            tx = {
                'nonce': w3.eth.get_transaction_count(mestra.address),
                'to': end,
                'value': w3.to_wei(valor, 'ether'),
                'gas': 21000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 137
            }
            assinado = w3.eth.account.sign_transaction(tx, pk_mestra)
            w3.eth.send_raw_transaction(assinado.raw_transaction)
            progresso.progress((i+1)/len(agentes))
        except Exception as e:
            st.error(f"Erro no envio {i}: {e}")
            break
    st.success("⛽ Gás distribuído com sucesso!")

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v12.9")
btc = pegar_preco()

# FALLBACK: Se não houver sinal, permite manual
if btc is None:
    st.error("⚠️ SEM SINAL DE REDE.")
    btc_input = st.number_input("DIGITE O PREÇO ATUAL PARA OPERAR MANUALMENTE:", value=0.0)
    if btc_input > 0:
        btc = btc_input

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}", delta="OPERANDO")
    
    with st.sidebar:
        st.header("⚙️ CONFIGURAÇÕES")
        if "pk_gas" not in st.session_state: st.session_state.pk_gas = ""
        st.session_state.pk_gas = st.text_input("Sua PK Mestra:", value=st.session_state.pk_gas, type="password")
        
        tp = st.slider("Take Profit (%)", 0.1, 5.0, 1.5)
        
        if st.button("🚀 REGERAR SNIPERS"):
            db.execute("DELETE FROM agentes_v6")
            for i in range(50):
                acc = Account.create()
                db.execute("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao, last_hash) VALUES (?,?,?,?,?,?,?,?)",
                           (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), btc - (i * 150), "VIGILANCIA", 0.0, "Pronto", ""))
            db.commit()
            st.rerun()

        st.divider()
        valor_dist = st.number_input("POL p/ Sniper:", value=0.1)
        if st.button("💸 DIVIDIR POL"):
            if st.session_state.pk_gas: dividir_pol(st.session_state.pk_gas, valor_dist)
            else: st.warning("Coloque a PK Mestra!")

    # --- MOTOR DE TRADE ATIVO INFINITO ---
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    for ag in agentes:
        id_ag, nome, _, _, alvo, status, p_compra, _, _ = ag
        # Compra no Grid
        if btc <= alvo and status == "VIGILANCIA":
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, last_hash='TX_PENDENTE' WHERE id=?", (btc, id_ag))
            db.commit()
        # Take Profit Ativo Infinito
        elif status == "COMPRADO" and btc >= p_compra * (1 + (tp/100)):
            db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, last_hash='TX_SUCCESS' WHERE id=?", (id_ag,))
            db.commit()

    # --- TABS ---
    t1, t2 = st.tabs(["🎯 Monitor", "📜 Histórico"])
    with t1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.caption(f"S: {a[5]}")
    with t2:
        df = pd.DataFrame(agentes, columns=['ID', 'Nome', 'End', 'Key', 'Alvo', 'Status', 'P.Compra', 'Ação', 'Hash'])
        for _, row in df[df['Hash'] != ""].iterrows():
            st.code(f"{row['Nome']} | Hash: {row['Hash']}")
            if "0x" in str(row['Hash']): st.link_button("Ver no PolygonScan", f"{EXPLORER_URL}{row['Hash']}")

else:
    st.info("Aguardando conexão ou entrada manual do preço...")

time.sleep(15)
st.rerun()