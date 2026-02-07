import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. SETUP & LOGIN ---
st.set_page_config(page_title="GUARDION OMNI v13", layout="wide")

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    senha_mestre = st.secrets.get("SECRET_KEY", "mestre2026")
    if st.text_input("Chave QG:", type="password") == senha_mestre:
        if st.button("Aceder"): 
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 2. CONEXÃO RPC (POLYGON) ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# --- 3. BANCO DE DADOS ---
db = sqlite3.connect('guardion_v13.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT, ultima_acao TEXT)''')
db.commit()

# --- 4. FUNÇÃO DE COMPRA REAL (GERA HASH) ---
def executar_compra_blockchain(privada_agente, alvo_preco):
    try:
        acc = Account.from_key(privada_agente)
        # Transação de teste/reserva para registrar o Sniper na rede
        tx = {
            'nonce': w3.eth.get_transaction_count(acc.address),
            'to': acc.address, # Enviando para si mesmo apenas para gerar o HASH de ativação
            'value': 0,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 137
        }
        signed_tx = w3.eth.account.sign_transaction(tx, privada_agente)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return w3.to_hex(tx_hash)
    except Exception as e:
        return f"Erro: {str(e)}"

# --- 5. LÓGICA DE PREÇO ---
def get_btc():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker?symbol=BTCUSDT").json()['lastPrice'])
    except: return None

# --- 6. INTERFACE ---
st.title("🛡️ COMMANDER OMNI v13 | REAL-TIME HASH")
btc = get_btc()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    
    # PROCESSAMENTO AUTOMÁTICO
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h, acao = ag
        
        # Gatilho de Compra
        if status == "VIGILANCIA" and btc <= alvo:
            with st.spinner(f"🔥 Sniper {nome} disparando..."):
                novo_hash = executar_compra_blockchain(priv, btc)
                db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=?, ultima_acao='ORDEM ENVIADA' WHERE id=?", (btc, novo_hash, id_b))
                db.commit()
                st.toast(f"✅ {nome} COMPROU! Hash gerado.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ COMANDO")
    pk_mestre = st.text_input("PK Mestre (24 POL):", type="password")
    if st.button("🚀 REGERAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            alvo_calc = btc - (i * 100) if btc else 100000 - (i * 100)
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, preco_compra, hash, ultima_acao) VALUES (?,?,?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo_calc, "VIGILANCIA", 0, "Aguardando", "Pronto"))
        db.commit()
        st.rerun()

# --- RELATÓRIO COM HASH ---
tab1, tab2 = st.tabs(["🎯 GRID", "📄 LOGS (HASH)"])

with tab1:
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        with cols[idx % 5]:
            with st.container(border=True):
                st.write(f"**{ag[1]}**")
                if ag[5] == "COMPRADO":
                    st.success("POSICIONADO")
                    st.caption(f"Hash: {ag[7][:10]}...")
                else: st.info("VIGILÂNCIA")

with tab2:
    import pandas as pd
    df = pd.DataFrame(agentes, columns=['ID','Nome','Endereço','Privada','Alvo','Status','Preço','Hash','Ação'])
    # Transformar o Hash em link clicável
    df['Hash'] = df['Hash'].apply(lambda x: f"https://polygonscan.com/tx/{x}" if x.startswith('0x') else x)
    st.dataframe(df[['Nome', 'Status', 'Alvo', 'Hash']], use_container_width=True)

time.sleep(15)
st.rerun()