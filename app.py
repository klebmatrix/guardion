import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO ROBUSTA ---
RPC_URL = "https://polygon-rpc.com" 
W3 = Web3(Web3.HTTPProvider(RPC_URL))

st.set_page_config(page_title="GUARDION v20.0 - REAL WITHDRAW", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v20.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, lucro REAL)''')
db.commit()

# --- FUNÇÃO DE RETIRADA REAL (BRUTA) ---
def executar_saque_emergencia(privada_agente, carteira_destino):
    try:
        conta = Account.from_key(privada_agente)
        saldo = W3.eth.get_balance(conta.address)
        gas_price = int(W3.eth.gas_price * 1.5) # Paga mais para passar na frente
        custo_gas = gas_price * 21000
        
        if saldo > custo_gas:
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address),
                'to': carteira_destino,
                'value': saldo - custo_gas,
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': 137
            }
            assinada = W3.eth.account.sign_transaction(tx, privada_agente)
            tx_hash = W3.eth.send_raw_transaction(assinada.raw_transaction)
            return W3.to_hex(tx_hash)
        return "SALDO_INSUFICIENTE"
    except Exception as e:
        return f"ERRO: {str(e)}"

# --- INTERFACE ---
st.title("🛡️ GUARDION v20.0 | RETIRADA EM TEMPO REAL")

with st.sidebar:
    st.header("🎮 PAINEL DE CONTROLE")
    carteira_mestra = st.text_input("Sua Carteira (Destino Final):")
    st.divider()
    if st.button("🔥 GERAR 10 SNIPERS DE ELITE"):
        db.execute("DELETE FROM agentes")
        for i in range(10):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?)", (i, f"ELITE-{i+1:02d}", acc.address, acc.key.hex(), 0.0))
        db.commit()
        st.rerun()

# --- MONITOR DE OPERAÇÃO ---
snipers = db.execute("SELECT * FROM agentes").fetchall()

if not snipers:
    st.warning("⚠️ Gere os snipers no menu lateral.")
else:
    st.subheader("💰 SALDO E RETIRADA")
    
    cols = st.columns(2) # Duas colunas para ficar maior e mais fácil de clicar
    for i, s in enumerate(snipers):
        with cols[i % 2]:
            with st.container(border=True):
                # Consulta saldo real (apenas o necessário)
                try:
                    saldo_wei = W3.eth.get_balance(s[2])
                    saldo_pol = W3.from_wei(saldo_wei, 'ether')
                except: saldo_pol = 0.0
                
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**{s[1]}**")
                    st.write(f"Saldo: **{saldo_pol:.4f} POL**")
                    st.caption(f"End: `{s[2]}`")
                
                with c2:
                    # O BOTÃO DE RETIRADA AGORA É UM COMANDO DIRETO
                    if st.button(f"💸 RETIRAR", key=f"withdraw_{s[0]}"):
                        if not carteira_mestra:
                            st.error("Coloque a carteira de destino!")
                        else:
                            with st.spinner("Enviando..."):
                                resultado = executar_saque_emergencia(s[3], carteira_mestra)
                                if "0x" in resultado:
                                    st.success("ENVIADO!")
                                    st.caption(f"Hash: {resultado[:15]}...")
                                else:
                                    st.error(f"{resultado}")

st.divider()
st.info("💡 **Dica:** Se o botão 'Retirar' não funcionar, é porque o sniper não tem POL suficiente para pagar a taxa de rede (Gas).")

time.sleep(10)
st.rerun()