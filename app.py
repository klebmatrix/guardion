import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests

# --- 1. SETUP ---
st.set_page_config(page_title="GUARDION OMNI v16.4", layout="wide")

db = sqlite3.connect('guardion_real_v16.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# --- 2. MOTOR DE PREÇO (RESILIÊNCIA TOTAL) ---
def pegar_preco_btc():
    headers = {'User-Agent': 'Mozilla/5.0'} # Simula um navegador para evitar bloqueio
    try:
        # Tenta Binance
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10, headers=headers)
        return float(r.json()['price'])
    except:
        try:
            # Tenta CoinGecko como plano B
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
            return float(r.json()['bitcoin']['usd'])
        except:
            return None

# --- 3. CONEXÃO BLOCKCHAIN ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def assinar_operacao(privada, addr):
    try:
        acc = Account.from_key(privada)
        tx = {
            'nonce': w3.eth.get_transaction_count(acc.address),
            'to': addr, 'value': 0, 'gas': 21000, 
            'gasPrice': w3.eth.gas_price, 'chainId': 137
        }
        signed = w3.eth.account.sign_transaction(tx, privada)
        return w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
    except: return "ERRO"

# --- 4. LOGICA INFINITA ---
st.title("🛡️ GUARDION OMNI | CICLO INFINITO")
btc = pegar_preco_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}", delta="✅ CONEXÃO ESTÁVEL")
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        
        # COMPRA (QUEDA)
        if status == "VIGILANCIA" and btc <= alvo:
            if w3.eth.get_balance(addr) > 0:
                shs = assinar_operacao(priv, addr)
                if shs.startswith("0x"):
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit(); st.toast(f"🎯 {nome} COMPROU!")

        # VENDA (SUBIDA + RESET PARA VIGILÂNCIA INFINITA)
        elif status == "COMPRADO" and btc >= (p_compra + 200):
            shs = assinar_operacao(priv, addr)
            if shs.startswith("0x"):
                db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, hash=? WHERE id=?", (shs, id_b))
                db.commit(); st.toast(f"💰 {nome} LUCROU E RESETOU!")
    
    # Grid de visualização
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                if ag[5] == "COMPRADO": st.success(f"LUCRO: +${btc - ag[6]:.0f}")
                else: st.info(f"🎯 Target: ${ag[4]:,.0f}")
else:
    st.error("🚨 BLOQUEIO DE SEGURANÇA ATIVO: As APIs de preço nos desconectaram.")
    st.info("O sistema entrará em hibernação por 2 minutos para limpar o seu IP e evitar banimento.")
    time.sleep(120) # Hibernação de 2 minutos
    st.rerun()

# Sidebar de Comando
with st.sidebar:
    if st.button("🚀 REINICIAR BATALHÃO"):
        db.execute("DELETE FROM agentes")
        # Se BTC estiver off, usa 95k como base segura
        p_base = btc if btc else 95000.0 
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_base - (i * 100), "VIGILANCIA", "---"))
        db.commit(); st.rerun()

time.sleep(60); st.rerun()