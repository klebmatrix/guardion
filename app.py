
import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v16.6", layout="wide")

db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# --- 2. SISTEMA DE RPC ROTATIVO (ANTI-BLOQUEIO) ---
RPCS = [
    "https://polygon-rpc.com",
    "https://polygon.drpc.org",
    "https://1rpc.io/matic",
    "https://rpc-mainnet.maticvigil.com"
]

def conectar_w3():
    for url in RPCS:
        try:
            w3_test = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 5}))
            if w3_test.is_connected():
                return w3_test
        except:
            continue
    return None

w3 = conectar_w3()

# --- 3. PREÇO VIA ORÁCULO COM FALLBACK ---
def pegar_preco_seguro():
    if not w3: return None
    try:
        # Tenta via Oráculo Chainlink na Polygon (Direto na rede)
        btc_proxy = "0xc907E119666Ab23c568f4E9F06A3f2E10E4dd48E"
        abi = '[{"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}]'
        contract = w3.eth.contract(address=btc_proxy, abi=abi)
        return float(contract.functions.latestAnswer().call() / 10**8)
    except:
        # Fallback para API externa se o contrato falhar
        try:
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
            return float(r.json()['price'])
        except:
            return None

# --- 4. MOTOR INFINITO ---
st.title("🛡️ GUARDION OMNI | v16.6 INFINITO")
btc = pegar_preco_seguro()

if btc and w3:
    st.metric("BTC ATUAL", f"${btc:,.2f}", delta="✅ CONECTADO")
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        
        # Lógica de Compra e Venda Infinitas (Inalterada para manter o ciclo)
        if status == "VIGILANCIA" and btc <= alvo:
            try:
                if w3.eth.get_balance(addr) > 0:
                    tx = {'nonce': w3.eth.get_transaction_count(addr), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                    signed = w3.eth.account.sign_transaction(tx, priv)
                    shs = w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit(); st.toast(f"🎯 {nome} COMPROU!")
            except: pass
        
        elif status == "COMPRADO" and btc >= (p_compra + 200):
            try:
                tx = {'nonce': w3.eth.get_transaction_count(addr), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                shs = w3.to_hex(w3.eth.send_raw_transaction(w3.eth.account.sign_transaction(tx, priv).raw_transaction))
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit(); st.toast(f"💰 {nome} RESETOU!")
            except: pass

    # Visualização
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                if ag[5] == "COMPRADO": st.success("💰 EM POSIÇÃO")
                else: st.info(f"🎯 ${ag[4]:,.0f}")
else:
    st.error("🚨 FALHA TOTAL DE COMUNICAÇÃO: O sistema está trocando de servidor...")
    time.sleep(10)
    st.rerun()

# Sidebar para Gerar Snipers
with st.sidebar:
    if st.button("🚀 REGERAR SNIPERS"):
        db.execute("DELETE FROM agentes")
        p_base = btc if btc else 100000.0
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_base - (i * 100), "VIGILANCIA", "---"))
        db.commit(); st.rerun()

time.sleep(30); st.rerun()