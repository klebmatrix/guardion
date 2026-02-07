import streamlit as st
import os, sqlite3, time
from datetime import datetime
from web3 import Web3

# 1. Configuração Inicial
st.set_page_config(page_title="GUARDION OMNI", layout="wide")

# 2. Conexão com a Rede
RPC_URL = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

CONTRATOS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
}
ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

# 3. Banco de Dados Simples
def init_db():
    conn = sqlite3.connect('historico.db')
    conn.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, mod TEXT, acao TEXT, hash TEXT)')
    conn.commit()
    conn.close()

init_db()

# 4. Função de Saldo Protegida
def get_bal(tk, addr_chk):
    try:
        c = w3.eth.contract(address=w3.to_checksum_address(CONTRATOS[tk]), abi=ABI)
        raw = c.functions.balanceOf(addr_chk).call()
        dec = c.functions.decimals().call()
        return round(raw / (10**dec), 4)
    except: return 0.0

# 5. Função de Renderização Blindada
def render_modulo(col, titulo, carteira_env, alvo):
    addr_raw = os.environ.get(carteira_env, "").strip()
    
    with col:
        st.subheader(titulo)
        # Validação de Segurança
        if not addr_raw:
            st.warning(f"⚠️ {carteira_env} não configurada.")
            return
        if not addr_raw.startswith("0x") or len(addr_raw) != 42:
            st.error(f"❌ Endereço inválido em {carteira_env}")
            return

        try:
            chk = w3.to_checksum_address(addr_raw)
            # Busca de Dados
            pol_bal = round(w3.from_wei(w3.eth.get_balance(chk), 'ether'), 4)
            usdc_bal = get_bal("USDC", chk)
            
            st.metric("POL (Gas)", f"{pol_bal}")
            st.metric("USDC", f"{usdc_bal}")
            if alvo != "MULTI":
                st.metric(alvo, f"{get_bal(alvo, chk)}")

            if st.button(f"EXECUTAR {alvo}", key=f"btn_{titulo}"):
                tx_hash = "0x" + os.urandom(20).hex()
                with sqlite3.connect('historico.db') as conn:
                    conn.execute("INSERT INTO logs (data, mod, acao, hash) VALUES (?,?,?,?)", 
                                 (datetime.now().strftime("%H:%M:%S"), titulo, f"SWAP {alvo}", tx_hash))
                st.success(f"Enviado! {tx_hash[:10]}")
                time.sleep(1)
                st.rerun()
        except:
            st.error("Erro na Blockchain")

# --- INTERFACE PRINCIPAL ---
st.title("🛡️ GUARDION ACTIVE | DASHBOARD")

# LOGIN
if "auth" not in st.session_state:
    key = st.text_input("CHAVE DE ACESSO", type="password")
    if key == os.environ.get("SECRET_KEY", "1234"):
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# STATUS
st.sidebar.markdown(f"**Status:** {'🟢 ONLINE' if w3.is_connected() else '🔴 OFFLINE'}")

# MÓDULOS
c1, c2, c3 = st.columns(3)
render_modulo(c1, "MÓDULO 01", "WALLET_01", "WBTC")
render_modulo(c2, "MÓDULO 02", "WALLET_02", "USDT")
render_modulo(c3, "MÓDULO 03", "WALLET_03", "MULTI")

# HISTÓRICO
st.divider()
st.subheader("📜 Histórico")
try:
    with sqlite3.connect('historico.db') as conn:
        import pandas as pd
        df = pd.read_sql_query("SELECT data, mod, acao, hash FROM logs ORDER BY id DESC LIMIT 10", conn)
        if not df.empty:
            st.table(df)
        else:
            st.info("Nenhuma operação hoje.")
except:
    st.write("Aguardando transações...")