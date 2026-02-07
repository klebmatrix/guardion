import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- CONFIGURAÇÃO DE REDE ---
st.set_page_config(page_title="GUARDION OMNI v11", layout="wide")
RPC_URL = "https://polygon-rpc.com" 
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- BANCO DE DADOS (V3 - ESTÁVEL) ---
def init_db():
    conn = sqlite3.connect('guardion_v3.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS agentes 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo REAL, status TEXT, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- INTERFACE LATERAL (CONEXÃO E COMANDO) ---
with st.sidebar:
    st.header("🔐 QG DO COMANDO")
    pk_input = st.text_input("Sua PK_01 Conectada:", type="password", key="pk_main")
    
    PK_MESTRE = None
    if pk_input:
        try:
            pk_limpa = pk_input.strip().replace('"', '').replace("'", "")
            if not pk_limpa.startswith("0x") and len(pk_limpa) == 64: pk_limpa = "0x" + pk_limpa
            acc_mestre = Account.from_key(pk_limpa)
            PK_MESTRE = pk_limpa
            st.success(f"✅ MESTRE: {acc_mestre.address[:6]}...{acc_mestre.address[-4:]}")
        except: st.error("❌ Chave Inválida")

    st.divider()
    st.header("🏭 FÁBRICA DE SNIPERS")
    p_topo = st.number_input("Preço Alvo Inicial (USD):", value=102500.0)
    distancia = st.number_input("Distância entre Agentes ($):", value=200.0)
    
    if st.button("🚀 LANÇAR BATALHÃO (25)"):
        if not PK_MESTRE:
            st.warning("Conecte a PK primeiro!")
        else:
            db.execute("DELETE FROM agentes") # Limpa anterior
            novos = []
            for i in range(25):
                acc = Account.create()
                alvo = p_topo - (i * distancia)
                novos.append((f"SNIPER-{i+1:02d}", acc.address, acc.key.hex(), alvo, "VIGILANCIA", "Aguardando"))
            db.executemany("INSERT INTO agentes (nome, endereco, privada, alvo, status, ultima_acao) VALUES (?,?,?,?,?,?)", novos)
            db.commit()
            st.rerun()

# --- FUNÇÕES TÁTICAS ---
def get_btc_price():
    try:
        return requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price']
    except: return "---"

def abastecer_agente(addr_agente):
    if not PK_MESTRE: return
    try:
        if w3.eth.get_balance(addr_agente) < w3.to_wei(0.1, 'ether'):
            acc_m = Account.from_key(PK_MESTRE)
            tx = {
                'nonce': w3.eth.get_transaction_count(acc_m.address),
                'to': addr_agente, 'value': w3.to_wei(0.5, 'ether'), # Envia 0.5 POL
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            st.toast(f"⛽ Abastecendo {addr_agente[:6]}...", icon="🚀")
    except: pass

# --- PAINEL PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v11.0")
btc_atual = get_btc_price()

c1, c2, c3 = st.columns(3)
c1.metric("Preço BTC Atual", f"${btc_atual}")
c2.metric("Agentes em Campo", "25")
c3.metric("Rede", "Polygon Mainnet")

st.divider()

# Listagem de Agentes
agentes = db.execute("SELECT * FROM agentes").fetchall()
if agentes:
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            with st.container(border=True):
                # Pequeno delay para evitar erro de rede (HTTPError)
                time.sleep(0.05)
                try: saldo = round(w3.from_wei(w3.eth.get_balance(ag[2]), 'ether'), 2)
                except: saldo = 0.0
                
                st.write(f"**{ag[1]}**")
                st.caption(f"🎯 Alvo: ${ag[4]}")
                st.write(f"⛽ {saldo} POL")
                
                # Lógica de Abastecimento Automático
                if PK_MESTRE and saldo < 0.1:
                    abastecer_agente(ag[2])
else:
    st.info("O Batalhão está na reserva. Configure a PK e clique em Lançar.")

time.sleep(60)
st.rerun()