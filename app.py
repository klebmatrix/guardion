import streamlit as st
import os, sqlite3, time
from datetime import datetime
from web3 import Web3

st.set_page_config(page_title="GUARDION ACTIVE", layout="wide")

# Usando um RPC alternativo e mais rápido (Cloudflare ou Ankr)
RPC_URL = "https://polygon-rpc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

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
                # Tentativa de conexão com timeout
                chk = w3.to_checksum_address(clean_addr)
                
                # Pega POL
                pol_wei = w3.eth.get_balance(chk)
                pol = round(w3.from_wei(pol_wei, 'ether'), 4)
                
                # Pega USDC
                usdc = get_bal("USDC", chk)
                
                st.metric("POL (Gas)", f"{pol}")
                st.metric("USDC", f"{usdc}")
                
                if alvo != "MULTI":
                    st.metric(alvo, f"{get_bal(alvo, chk)}")
                
                st.button(f"EXECUTAR {titulo}", key=f"btn_{i}")
                
            except Exception as e:
                # Se der erro na rede, mostra o erro real para sabermos o que é
                st.error(f"Erro de Conexão: Verifique o RPC")
        else:
            st.error(f"Endereço Inválido")

st.divider()
st.write(f"Conectado via: {RPC_URL}")
if st.button("🔄 RECONECTAR"):
    st.rerun()