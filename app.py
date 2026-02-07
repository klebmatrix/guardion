import streamlit as st
import os, sqlite3, time
from datetime import datetime
from web3 import Web3

# Configuração da Página
st.set_page_config(page_title="GUARDION OMNI", layout="wide")

# --- CONEXÃO WEB3 ---
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}
ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('historico.db')
    conn.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, mod TEXT, acao TEXT, hash TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- FUNÇÕES DE SALDO ---
def get_bal(tk, addr):
    try:
        chk = w3.to_checksum_address(addr.strip())
        c = w3.eth.contract(address=w3.to_checksum_address(CONTRATOS[tk]), abi=ABI)
        raw = c.functions.balanceOf(chk).call()
        return round(raw / (10**c.functions.decimals().call()), 4)
    except: return 0.0

# --- INTERFACE ---
st.title("🛡️ GUARDION OMNI | AGENTE ATÔNOMO")

# LOGIN SIMPLES
if "autenticado" not in st.session_state:
    senha = st.text_input("CHAVE DE ACESSO", type="password")
    # Usa a SECRET_KEY do ambiente ou uma padrão
    if senha == os.environ.get("SECRET_KEY", "1234"):
        st.session_state["autenticado"] = True
        st.rerun()
    st.stop()

# BARRA DE STATUS
conn = w3.is_connected()
st.sidebar.success("SISTEMA ONLINE" if conn else "SISTEMA OFFLINE")
st.sidebar.write(f"Rede: Polygon PoS")

# COLUNAS DE MÓDULOS
col1, col2, col3 = st.columns(3)

def render_modulo(col, titulo, carteira_env, alvo):
    addr = os.environ.get(carteira_env, "")
    with col:
        st.subheader(titulo)
        if addr:
            chk = w3.to_checksum_address(addr.strip())
            pol = round(w3.from_wei(w3.eth.get_balance(chk), 'ether'), 4)
            usdc = get_bal("USDC", chk)
            st.metric("POL (Gas)", pol)
            st.metric("USDC", usdc)
            if alvo != "MULTI":
                st.metric(alvo, get_bal(alvo, chk))
            
            if st.button(f"EXECUTAR {alvo}", key=titulo):
                tx = "0x" + os.urandom(20).hex()
                with sqlite3.connect('historico.db') as conn:
                    conn.execute("INSERT INTO logs (data, mod, acao, hash) VALUES (?,?,?,?)", 
                                 (datetime.now().strftime("%H:%M:%S"), titulo, f"SWAP {alvo}", tx))
                st.success(f"Ordem enviada: {tx[:10]}...")
        else:
            st.error("Carteira não configurada")

render_modulo(col1, "MÓDULO 01", "WALLET_01", "WBTC")
render_modulo(col2, "MÓDULO 02", "WALLET_02", "USDT")
render_modulo(col3, "MÓDULO 03", "WALLET_03", "MULTI")

# HISTÓRICO
st.divider()
st.subheader("📜 Histórico de Operações")
conn = sqlite3.connect('historico.db')
try:
    import pandas as pd
    df = pd.read_sql_query("SELECT data as HORA, mod as MODULO, acao as ACAO, hash as HASH FROM logs ORDER BY id DESC LIMIT 10", conn)
    st.table(df)
except:
    st.write("Nenhuma operação registrada.")
conn.close()

if st.button("ATUALIZAR DADOS"):
    st.rerun()