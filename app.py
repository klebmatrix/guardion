import streamlit as st
import os, sqlite3, time
from datetime import datetime
from web3 import Web3

st.set_page_config(page_title="GUARDION ACTIVE", layout="wide")

# RPC da Cloudflare (Geralmente não cai e não bloqueia)
RPC_URL = "https://polygon-rpc.com" 
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 20}))

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

# LOGIN
if "auth" not in st.session_state:
    senha = st.text_input("CHAVE DE ACESSO", type="password")
    master_key = str(st.secrets.get("SECRET_KEY", "1234"))
    if senha == master_key:
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# TESTE DE CONEXÃO INICIAL
if not w3.is_connected():
    st.error("🔴 Sem resposta da rede Polygon. Tentando trocar de servidor...")
    w3 = Web3(Web3.HTTPProvider("https://polygon.llamarpc.com"))

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
        
        # BUSCA E LIMPEZA
        raw_addr = str(st.secrets.get(env_var, ""))
        clean_addr = raw_addr.strip().replace('"', '').replace("'", "")
        
        if clean_addr.startswith("0x") and len(clean_addr) == 42:
            try:
                chk = w3.to_checksum_address(clean_addr)
                
                # Pega POL e USDC
                pol = round(w3.from_wei(w3.eth.get_balance(chk), 'ether'), 4)
                usdc = get_bal("USDC", chk)
                
                st.metric("POL (Gas)", f"{pol}")
                st.metric("USDC", f"{usdc}")
                
                if alvo != "MULTI":
                    st.metric(alvo, f"{get_bal(alvo, chk)}")
                
                st.button(f"EXECUTAR {titulo}", key=f"btn_{i}")
                
            except Exception as e:
                st.error(f"Erro ao ler saldo. Tente atualizar.")
        else:
            st.warning(f"Aguardando {env_var}")

st.divider()
st.info(f"Conexão ativa: {w3.is_connected()}")
if st.button("🔄 FORÇAR RECONEXÃO"):
    st.rerun()