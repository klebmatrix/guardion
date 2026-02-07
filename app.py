import streamlit as st
import os, sqlite3, time
from datetime import datetime
from web3 import Web3

st.set_page_config(page_title="GUARDION ACTIVE", layout="wide")

# Lista de servidores para rodízio (Se um cair, o outro assume)
RPCS = [
    "https://polygon-rpc.com",
    "https://polygon.llamarpc.com",
    "https://1rpc.io/matic",
    "https://rpc.ankr.com/polygon"
]

def conectar():
    for url in RPCS:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                return w3, url
        except:
            continue
    return None, None

w3, rpc_ativa = conectar()

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}
ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

def get_bal(tk, addr_chk):
    try:
        c = w3.eth.contract(address=w3.to_checksum_address(CONTRATOS[tk]), abi=ABI)
        raw = c.functions.balanceOf(addr_chk).call()
        dec = c.functions.decimals().call()
        return round(raw / (10**dec), 4)
    except: return 0.0

# --- INTERFACE ---
st.title("🛡️ GUARDION ACTIVE | DASHBOARD")

if "auth" not in st.session_state:
    senha = st.text_input("CHAVE DE ACESSO", type="password")
    if senha == str(st.secrets.get("SECRET_KEY", "1234")):
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

if not w3:
    st.error("🔴 Bloqueio de Rede: Todos os servidores Polygon falharam. O Streamlit está impedindo a conexão.")
    if st.button("TENTAR NOVAMENTE"):
        st.rerun()
    st.stop()

# MÓDULOS
cols = st.columns(3)
modulos = [
    ("MÓDULO 01", "WALLET_01", "WBTC"),
    ("MÓDULO 02", "WALLET_02", "USDT"),
    ("MÓDULO 03", "WALLET_03", "MULTI")
]

for i, (titulo, env_var, alvo) in enumerate(modulos):
    with cols[i]:
        st.subheader(titulo)
        addr = str(st.secrets.get(env_var, "")).strip().replace('"', '').replace("'", "")
        
        if len(addr) == 42 and addr.startswith("0x"):
            try:
                chk = w3.to_checksum_address(addr)
                pol = round(w3.from_wei(w3.eth.get_balance(chk), 'ether'), 4)
                usdc = get_bal("USDC", chk)
                st.metric("POL (Gas)", f"{pol}")
                st.metric("USDC", f"{usdc}")
                if alvo != "MULTI":
                    st.metric(alvo, f"{get_bal(alvo, chk)}")
                st.button(f"EXECUTAR {titulo}", key=f"btn_{i}")
            except:
                st.error("Erro ao ler dados")
        else:
            st.warning(f"Configurar {env_var}")

st.divider()
st.caption(f"Conectado via: {rpc_ativa}")