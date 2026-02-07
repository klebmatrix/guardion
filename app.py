import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
st.set_page_config(page_title="GUARDION OMNI v15.0", layout="wide")

# Inicialização do Banco de Dados
db = sqlite3.connect('guardion_real_v15.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# Carregar agentes globalmente para evitar NameError
agentes = db.execute("SELECT * FROM agentes").fetchall()

# --- 2. ACESSO ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🛡️ QG GUARDION REAL")
    senha = st.text_input("Chave Mestre:", type="password")
    if st.button("DESBLOQUEAR"):
        if senha == st.secrets.get("SECRET_KEY", "mestre2026"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 3. CONEXÃO BLOCKCHAIN ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def pegar_preco_btc():
    try:
        return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price'])
    except: return None

# ABASTECIMENTO COM GESTÃO DE NONCE REAL
def abastecer_agentes(pk_mestre):
    try:
        mestre_acc = Account.from_key(pk_mestre)
        alvo_agentes = db.execute("SELECT endereco FROM agentes LIMIT 10").fetchall()
        
        # Pega o nonce atualizado direto da rede
        current_nonce = w3.eth.get_transaction_count(mestre_acc.address)
        
        for ag in alvo_agentes:
            tx = {
                'nonce': current_nonce,
                'to': ag[0],
                'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000,
                'gasPrice': int(w3.eth.gas_price * 1.3), # Taxa prioritária
                'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, pk_mestre)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            current_nonce += 1 # Incrementa para a próxima transação
            time.sleep(1) 
        return True
    except Exception as e:
        st.sidebar.error(f"Erro: {str(e)}")
        return False

# COMPRA REAL (GERA SHS)
def operacao_real(privada_agente):
    try:
        acc = Account.from_key(privada_agente)
        if w3.eth.get_balance(acc.address) < w3.to_wei(0.005, 'ether'):
            return "SEM_GAS"
        
        tx = {
            'nonce': w3.eth.get_transaction_count(acc.address),
            'to': acc.address,
            'value': 0,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 137
        }
        signed = w3.eth.account.sign_transaction(tx, privada_agente)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return w3.to_hex(tx_hash)
    except: return "ERRO_REDE"

# --- 4. INTERFACE ---
st.title("🛡️ COMMANDER OMNI v15.0")
btc = pegar_preco_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        if status == "VIGILANCIA" and btc <= alvo:
            shs = operacao_real(priv)
            if shs.startswith("0x"):
                db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                db.commit()
                st.toast(f"✅ {nome} COMPROU!")

# --- 5. COMANDOS ---
with st.sidebar:
    st.header("⚙️ COMANDO CENTRAL")
    pk_m = st.text_input("PK_01 Mestre:", type="password")
    
    if st.button("🚀 GERAR NOVO BATALHÃO"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            alvo_calc = btc - (i * 100) if btc else 100000 - (i * 100)
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo_calc, "VIGILANCIA", "---"))
        db.commit()
        st.rerun()

    if st.button("⛽ ABASTECER (0.5 POL)"):
        if abastecer_agentes(pk_m): st.success("Abastecimento em curso!")
        else: st.error("Falha no envio.")

# --- 6. PAINEL ---
t1, t2 = st.tabs(["🎯 GRID DE CAMPO", "📄 LOGS & SHS"])

with t1:
    if agentes:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    if "0x" in str(ag[7]): st.success("REALIZADO")
                    elif ag[7] == "SEM_GAS": st.warning("FALTA POL")
                    else: st.info(f"🎯 ${ag[4]:,.0f}")

with t2:
    if agentes:
        import pandas as pd
        df = pd.DataFrame(agentes, columns=['ID','Nome','Endereço','Privada','Alvo','Status','Preço','Hash'])
        df['PolygonScan'] = df['Hash'].apply(lambda x: f"https://polygonscan.com/tx/{x}" if x.startswith('0x') else x)
        st.dataframe(df[['Nome', 'Status', 'Alvo', 'PolygonScan', 'Endereço']], width='stretch')

time.sleep(20); st.rerun()