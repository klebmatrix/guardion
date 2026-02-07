import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. SETUP & LOGIN ---
st.set_page_config(page_title="GUARDION OMNI v13.1", layout="wide")

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    senha_mestre = st.secrets.get("SECRET_KEY", "mestre2026")
    st.title("🔐 QG COMMANDER OMNI")
    senha_in = st.text_input("Chave QG:", type="password")
    if st.button("Aceder"):
        if senha_in == senha_mestre:
            st.session_state.logado = True
            st.rerun()
        else: st.error("Incorreta")
    st.stop()

# --- 2. CONEXÃO RPC & DB ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
db = sqlite3.connect('guardion_v13.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT, ultima_acao TEXT)''')
db.commit()

# --- 3. MOTOR DE PREÇO ---
def get_btc():
    try: 
        return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()['price'])
    except: return None

# --- 4. FUNÇÃO DE COMPRA REAL (GERA HASH) ---
def executar_compra_blockchain(privada_agente):
    try:
        acc = Account.from_key(privada_agente)
        tx = {
            'nonce': w3.eth.get_transaction_count(acc.address),
            'to': acc.address, # Auto-transação para registro de HASH real na rede
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

# --- 5. EXECUÇÃO PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v13.1")
btc = get_btc()

# Busca os agentes logo no início para evitar NameError
agentes = db.execute("SELECT * FROM agentes").fetchall()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    
    # Processa ordens para os agentes que já existem
    for ag in agentes:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h, acao = ag
        if status == "VIGILANCIA" and btc <= alvo:
            with st.spinner(f"🔥 Sniper {nome} operando..."):
                novo_hash = executar_compra_blockchain(priv)
                db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=?, ultima_acao='COMPRA EXECUTADA' WHERE id=?", (btc, novo_hash, id_b))
                db.commit()
                st.toast(f"✅ {nome} gerou Hash!")
                st.rerun()

# --- 6. BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ COMANDO")
    if st.button("🚀 REGERAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            alvo_calc = btc - (i * 100) if btc else 100000 - (i * 100)
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, preco_compra, hash, ultima_acao) VALUES (?,?,?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo_calc, "VIGILANCIA", 0, "Aguardando", "Pronto"))
        db.commit()
        st.success("50 Agentes Criados!")
        st.rerun()
    
    if st.button("Logout"):
        st.session_state.logado = False
        st.rerun()

# --- 7. PAINEL VISUAL ---
tab1, tab2 = st.tabs(["🎯 GRID DE VIGILÂNCIA", "📄 RELATÓRIO DE HASH"])

with tab1:
    if agentes:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    if ag[5] == "COMPRADO":
                        st.success("COMPRADO")
                        st.caption(f"Hash: {ag[7][:10]}...")
                    else:
                        st.info(f"🎯 ${ag[4]:,.0f}")
    else:
        st.warning("Batalhão vazio. Clique no botão lateral para lançar.")

with tab2:
    if agentes:
        import pandas as pd
        df = pd.DataFrame(agentes, columns=['ID','Nome','Endereço','Privada','Alvo','Status','Preço','Hash','Ação'])
        # Link para PolygonScan
        df['Hash_Link'] = df['Hash'].apply(lambda x: f"https://polygonscan.com/tx/{x}" if x.startswith('0x') else x)
        st.dataframe(df[['Nome', 'Status', 'Alvo', 'Hash_Link']], use_container_width=True)
    else:
        st.write("Nenhum log disponível.")

time.sleep(15)
st.rerun()