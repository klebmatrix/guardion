import streamlit as st
import os, sqlite3, time
from datetime import datetime
from web3 import Web3

# 1. Configuração da Página
st.set_page_config(page_title="GUARDION ACTIVE", layout="wide")

# 2. Conexão Polygon (RPC Estável)
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}
ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

# 3. Funções de Apoio
def init_db():
    conn = sqlite3.connect('historico.db')
    conn.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, mod TEXT, acao TEXT, hash TEXT)')
    conn.commit()
    conn.close()

def get_bal(tk, addr_chk):
    try:
        c = w3.eth.contract(address=w3.to_checksum_address(CONTRATOS[tk]), abi=ABI)
        raw = c.functions.balanceOf(addr_chk).call()
        dec = c.functions.decimals().call()
        return round(raw / (10**dec), 4)
    except: return 0.0

init_db()

# --- INTERFACE ---
st.title("🛡️ GUARDION ACTIVE | DASHBOARD")

# LOGIN (Puxa do Secrets)
if "auth" not in st.session_state:
    senha = st.text_input("CHAVE DE ACESSO", type="password")
    if senha == st.secrets.get("SECRET_KEY", "1234"):
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# BARRA LATERAL
st.sidebar.header("Status do Agente")
st.sidebar.success("CONECTADO À POLYGON" if w3.is_connected() else "ERRO DE CONEXÃO")

# 4. MÓDULOS (Onde os cards aparecem)
cols = st.columns(3)
modulos = [
    ("MÓDULO 01", "WALLET_01", "WBTC"),
    ("MÓDULO 02", "WALLET_02", "USDT"),
    ("MÓDULO 03", "WALLET_03", "MULTI")
]

for i, (titulo, env_var, alvo) in enumerate(modulos):
    with cols[i]:
        st.subheader(titulo)
        # Tenta pegar o endereço do Secrets do Streamlit
        addr = st.secrets.get(env_var, "").strip()
        
        if not addr:
            st.warning(f"Configurar {env_var} nos Secrets")
        elif len(addr) > 42:
            st.error("⚠️ Você colou a Private Key! Troque pelo Endereço (0x...)")
        else:
            try:
                chk = w3.to_checksum_address(addr)
                pol = round(w3.from_wei(w3.eth.get_balance(chk), 'ether'), 4)
                usdc = get_bal("USDC", chk)
                
                st.metric("POL (Gas)", f"{pol}")
                st.metric("USDC", f"{usdc}")
                if alvo != "MULTI":
                    st.metric(alvo, f"{get_bal(alvo, chk)}")
                
                if st.button(f"EXECUTAR {titulo}", key=f"btn_{i}"):
                    tx = "0x" + os.urandom(20).hex()
                    with sqlite3.connect('historico.db') as conn:
                        conn.execute("INSERT INTO logs (data, mod, acao, hash) VALUES (?,?,?,?)", 
                                     (datetime.now().strftime("%H:%M:%S"), titulo, f"SWAP {alvo}", tx))
                    st.success("Ordem Registrada!")
                    time.sleep(1)
                    st.rerun()
            except:
                st.error("Endereço Inválido")

# 5. HISTÓRICO
st.divider()
st.subheader("📜 Histórico Recente")
try:
    with sqlite3.connect('historico.db') as conn:
        import pandas as pd
        df = pd.read_sql_query("SELECT data, mod, acao, hash FROM logs ORDER BY id DESC LIMIT 10", conn)
        st.dataframe(df, use_container_width=True)
except:
    st.info("Nenhuma operação registrada ainda.")