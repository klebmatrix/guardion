import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v15.6 REAL", layout="wide")

db = sqlite3.connect('guardion_real_v15.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

agentes_raw = db.execute("SELECT * FROM agentes").fetchall()

# --- 2. LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🛡️ QG GUARDION REAL")
    senha = st.text_input("Chave Mestre:", type="password")
    if st.button("DESBLOQUEAR"):
        if senha == st.secrets.get("SECRET_KEY", "mestre2026"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 3. CONEXÃO RPC RESILIENTE ---
# Trocando para um provedor mais estável para evitar o erro -32090
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com")) 

def pegar_preco_btc():
    try: 
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3)
        return float(r.json()['price'])
    except: return None

# ABASTECIMENTO COM DELAY PARA EVITAR RATE LIMIT
def abastecer_agentes(pk_mestre):
    try:
        mestre_acc = Account.from_key(pk_mestre)
        alvo_agentes = db.execute("SELECT endereco FROM agentes LIMIT 10").fetchall()
        
        # Pega o nonce pendente para evitar travamentos
        nonce = w3.eth.get_transaction_count(mestre_acc.address, 'pending')
        
        progresso = st.sidebar.progress(0)
        for i, ag in enumerate(alvo_agentes):
            tx = {
                'nonce': nonce,
                'to': ag[0],
                'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000,
                'gasPrice': int(w3.eth.gas_price * 1.5),
                'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, pk_mestre)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            
            nonce += 1
            progresso.progress((i + 1) / len(alvo_agentes))
            # ESPERA 4 SEGUNDOS entre cada envio para a rede não nos bloquear
            time.sleep(4) 
        return True
    except Exception as e:
        st.sidebar.error(f"Rede: {str(e)[:30]}")
        return False

# --- 4. MOTOR DE EXECUÇÃO ---
st.title("🛡️ COMMANDER OMNI v15.6")
btc = pegar_preco_btc()

if btc:
    st.metric("BTC/USDT ATUAL", f"${btc:,.2f}")
    
    # Processamento otimizado
    for ag in agentes_raw:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        # Só checa a rede se o preço bater ou estiver muito perto (economia de RPC)
        if status == "VIGILANCIA" and btc <= (alvo + 10):
            try:
                saldo = w3.eth.get_balance(addr)
                if btc <= alvo and saldo > 0:
                    tx = {'nonce': w3.eth.get_transaction_count(addr), 'to': addr, 'value': 0, 'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137}
                    signed = w3.eth.account.sign_transaction(tx, priv)
                    shs = w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit()
            except: continue

# --- 5. COMANDOS ---
with st.sidebar:
    st.header("⚙️ COMANDO")
    pk_m = st.text_input("Sua PK (22 POL):", type="password")
    
    if st.button("🚀 GERAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            alvo_calc = btc - (i * 100) if btc else 100000 - (i * 100)
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo_calc, "VIGILANCIA", "---"))
        db.commit()
        st.rerun()

    if st.button("⛽ ABASTECER AGENTES"):
        if pk_m:
            with st.spinner("Enviando POL com cautela..."):
                if abastecer_agentes(pk_m): st.success("Sucesso!")
        else: st.warning("Falta PK")

# --- 6. TABELAS ---
t1, t2 = st.tabs(["🎯 GRID", "📄 LOGS"])
with t1:
    if agentes_raw:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes_raw):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    if "0x" in str(ag[7]): st.success("REALIZADO ✅")
                    else: st.info(f"🎯 ${ag[4]:,.0f}")

with t2:
    if agentes_raw:
        import pandas as pd
        df = pd.DataFrame(agentes_raw, columns=['ID','Nome','Endereço','Privada','Alvo','Status','Preço','Hash'])
        st.dataframe(df[['Nome', 'Status', 'Alvo', 'Hash', 'Endereço']], width='stretch')

# Refresh mais lento para evitar bloqueio do servidor
time.sleep(60)
st.rerun()