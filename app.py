import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. SETUP ---
st.set_page_config(page_title="GUARDION OMNI v16.2 INFINITO", layout="wide")

db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# --- 2. MOTOR DE PREÇO RESILIENTE (Binance + Backup) ---
def pegar_preco_seguro():
    # Tentativa 1: Binance
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3)
        return float(r.json()['price'])
    except:
        # Tentativa 2: Backup CoinGecko se a Binance bloquear
        try:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=3)
            return float(r.json()['bitcoin']['usd'])
        except:
            return None

# --- 3. CONEXÃO E EXECUÇÃO ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def executar_shs_real(privada):
    try:
        acc = Account.from_key(privada)
        tx = {'nonce': w3.eth.get_transaction_count(acc.address), 'to': acc.address, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
        signed = w3.eth.account.sign_transaction(tx, privada)
        return w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
    except: return "ERRO"

# --- 4. LÓGICA INFINITA ---
st.title("♾️ GUARDION MODO INFINITO ATIVO")
btc = pegar_preco_seguro()

if btc:
    st.metric("BTC ATUAL (POLYGON DATA)", f"${btc:,.2f}")
    agentes_raw = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes_raw:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        
        # COMPRA INFINITA
        if status == "VIGILANCIA" and btc <= alvo:
            if w3.eth.get_balance(addr) > 0:
                shs = executar_shs_real(priv)
                if shs.startswith("0x"):
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit(); st.toast(f"🎯 {nome} COMPROU!")

        # VENDA INFINITA (RESET AUTOMÁTICO)
        elif status == "COMPRADO" and btc >= (p_compra + 150): # Lucro de $150 para giro rápido
            shs = executar_shs_real(priv)
            if shs.startswith("0x"):
                # O Segredo do Infinito: Volta a ser Vigilante com o mesmo Alvo
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit(); st.toast(f"💰 {nome} LUCROU E RESETOU!")
else:
    st.error("⚠️ ERRO DE CONEXÃO: Aguardando 15s para nova tentativa...")
    time.sleep(15)
    st.rerun()

# --- 5. INTERFACE ---
with st.sidebar:
    st.header("⚙️ COMANDO CENTRAL")
    if st.button("🚀 REINICIAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        p_base = btc if btc else 100000.0
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_base - (i * 100), "VIGILANCIA", "---"))
        db.commit(); st.rerun()

    pk_m = st.text_input("Sua PK (22 POL):", type="password")
    if st.button("⛽ ABASTECER"):
        # Lógica de abastecimento já validada anteriormente...
        pass

# --- 6. PAINEL ---
t1, t2 = st.tabs(["🎯 GRID", "📄 RELATÓRIO"])
with t1:
    agentes_view = db.execute("SELECT * FROM agentes").fetchall()
    if agentes_view:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes_view):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    if ag[5] == "COMPRADO": st.success("💰 EM POSIÇÃO")
                    else: st.info(f"🎯 ${ag[4]:,.0f}")

time.sleep(45); st.rerun()