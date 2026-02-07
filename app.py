import streamlit as st
from web3 import Web3
from eth_account import Account

# --- LEITURA DIRETA E LIMPA ---
def check_pk():
    try:
        # Tenta ler exatamente o que está no segredo
        raw_pk = st.secrets["PK_MESTRE"]
        clean_pk = str(raw_pk).strip().replace('"', '').replace("'", "")
        if not clean_pk.startswith("0x"):
            clean_pk = "0x" + clean_pk
        return clean_pk
    except:
        return None

PK_MESTRE = check_pk()

# --- INTERFACE DE STATUS ---
st.title("🛡️ COMMANDER OMNI | SETUP")

if not PK_MESTRE:
    st.error("🚨 ERRO DE CONFIGURAÇÃO: A chave não foi encontrada ou o formato TOML está errado.")
    st.info("No campo Secrets, escreva exatamente assim: PK_MESTRE = \"SUA_CHAVE\"")
else:
    try:
        acc = Account.from_key(PK_MESTRE)
        st.success(f"✅ CONECTADO: {acc.address}")
        st.write("O sistema de abastecimento de 25 agentes está pronto para operar.")
    except Exception as e:
        st.error(f"❌ CHAVE INVÁLIDA: O texto fornecido não é uma chave privada válida. Erro: {e}")

st.divider()
st.caption("Dica: Se mudar o Secret agora, clique em 'Save' e aguarde o app reiniciar.")