import streamlit as st
from web3 import Web3

st.set_page_config(page_title="GUARDION", layout="wide")

# RPC super estável da Cloudflare
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# Interface
st.title("🛡️ GUARDION ACTIVE")

# Módulos
cols = st.columns(3)
modulos = [("MÓDULO 01", "WALLET_01"), ("MÓDULO 02", "WALLET_02"), ("MÓDULO 03", "WALLET_03")]

for i, (titulo, env_var) in enumerate(modulos):
    with cols[i]:
        st.subheader(titulo)
        # Puxa o endereço e limpa
        addr = st.secrets.get(env_var, "").strip().replace('"', '').replace("'", "")
        
        if addr:
            try:
                # Validação de Checksum
                chk_addr = w3.to_checksum_address(addr)
                
                # Tenta ler apenas o POL (Saldo da Moeda Nativa)
                balance_wei = w3.eth.get_balance(chk_addr)
                balance_pol = w3.from_wei(balance_wei, 'ether')
                
                st.metric("POL (Gas)", f"{balance_pol:.4f}")
                st.write(f"✅ Conectado: {chk_addr[:6]}...{chk_addr[-4:]}")
                
            except Exception as e:
                st.error(f"Erro técnico: {str(e)[:50]}")
        else:
            st.warning(f"Falta configurar {env_var}")

if st.button("🔄 TENTAR NOVAMENTE"):
    st.rerun()