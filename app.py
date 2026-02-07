import streamlit as st
from web3 import Web3
from eth_account import Account
import time

# --- SETUP DA REDE ---
st.set_page_config(page_title="GUARDION INDUSTRIAL", layout="wide")
# Usando um RPC alternativo para evitar bloqueios
w3 = Web3(Web3.HTTPProvider("https://polygon.drpc.org"))

st.title("🛡️ COMMANDER OMNI | v10.9")

# --- ÁREA DE CONEXÃO (SEM SECRETS) ---
with st.sidebar:
    st.header("🔐 Acesso Mestre")
    # Usamos uma chave de sessão para garantir que o input seja processado
    pk_raw = st.text_input("Cole sua PK_01 aqui:", type="password", key="pk_input_main")
    
    btn_conectar = st.button("CONECTAR AGORA")

# --- LÓGICA DE VALIDAÇÃO ---
if pk_raw or btn_conectar:
    try:
        # Limpeza radical da string
        pk_clean = str(pk_raw).strip().replace('"', '').replace("'", "").replace(" ", "")
        
        if len(pk_clean) == 64 and not pk_clean.startswith("0x"):
            pk_clean = "0x" + pk_clean
            
        # Teste de conexão real
        acc = Account.from_key(pk_clean)
        saldo_wei = w3.eth.get_balance(acc.address)
        saldo_pol = round(w3.from_wei(saldo_wei, 'ether'), 2)
        
        st.success(f"✅ Conectado à Wallet: {acc.address}")
        
        c1, c2 = st.columns(2)
        c1.metric("Saldo na Mestre", f"{saldo_pol} POL")
        
        if saldo_pol < 1.0:
            st.warning("⚠️ Saldo baixo para abastecer 25 agentes.")
            
        # --- SEÇÃO DE COMANDO ---
        st.divider()
        st.subheader("🚀 Comando de Batalhão")
        if st.button("GERAR ENDEREÇOS DOS 25 AGENTES"):
            st.info("Gerando chaves efêmeras para operação...")
            for i in range(25):
                novo_agente = Account.create()
                st.code(f"Agente {i+1}: {novo_agente.address}", language="text")
                # Aqui você enviaria os 0.5 POL para cada um
                
    except Exception as e:
        st.error(f"❌ Erro na Chave: Verifique se copiou todos os 64 caracteres. (Erro: {e})")
else:
    st.info("Aguardando inserção da Chave Privada (PK_01) na barra lateral para iniciar.")

# Rodapé Técnico
st.divider()
st.caption("Conectado via Polygon dRPC Mainnet")