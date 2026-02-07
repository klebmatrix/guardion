import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- RPC RESERVA (Para não travar no erro -32090) ---
RPC_RESERVA = "https://rpc-mainnet.maticvigil.com" 
W3 = Web3(Web3.HTTPProvider(RPC_RESERVA))

st.set_page_config(page_title="GUARDION v18.1 - ELITE", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v18_1.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, p_compra REAL, lucro_real REAL)''')
db.commit()

# --- FUNÇÃO DE ABASTECIMENTO (FLUXO CONTÍNUO) ---
def abastecer_elite(pk_mestra, lista):
    conta = Account.from_key(pk_mestra)
    status_progresso = st.empty()
    for i, ag in enumerate(lista):
        status_progresso.info(f"🚀 Enviando POL para {ag[1]}...")
        try:
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address),
                'to': ag[2],
                'value': W3.to_wei(0.5, 'ether'), # Envia 0.5 POL para cada
                'gas': 21000,
                'gasPrice': int(W3.eth.gas_price * 1.5),
                'chainId': 137
            }
            assinada = W3.eth.account.sign_transaction(tx, pk_mestra)
            W3.eth.send_raw_transaction(assinada.raw_transaction)
            time.sleep(5) # Pausa de 5s para a rede não te banir de novo
        except Exception as e:
            st.error(f"Erro no envio: {e}")
            break
    st.success("✅ ELITE ABASTECIDA!")

# --- UI ---
st.title("🛡️ ELITE COMMANDER v18.1")
st.warning("⚠️ MODO 10 SNIPERS: Menos requisições = Zero Travamento na Rede.")

col1, col2 = st.columns(2)
with col1:
    pk = st.text_input("🔑 Private Key (Origem):", type="password")
with col2:
    destino = st.text_input("🎯 Carteira Destino:")

c_btn1, c_btn2 = st.columns(2)
with c_btn1:
    if st.button("🔄 1. GERAR 10 SNIPERS DE ELITE", use_container_width=True):
        db.execute("DELETE FROM agentes")
        for i in range(10): # Reduzido para 10 para estabilidade total
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?)",
                       (i, f"ELITE-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0))
        db.commit()
        st.rerun()

with c_btn2:
    if st.button("🚀 2. ABASTECER ELITE AGORA", use_container_width=True):
        snipers = db.execute("SELECT * FROM agentes").fetchall()
        if pk and snipers:
            abastecer_elite(pk, snipers)
        else: st.error("Gere os snipers ou insira a chave!")

st.divider()

# --- MONITOR DE SALDO (SÓ ATUALIZA COM CLIQUE PARA NÃO TRAVAR) ---
st.subheader("📊 MONITOR DA TROPA")
snipers_list = db.execute("SELECT * FROM agentes").fetchall()

if not snipers_list:
    st.info("Clique em 'Gerar 10 Snipers' para começar.")
else:
    cols = st.columns(5)
    for i, s in enumerate(snipers_list):
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"**{s[1]}**")
                st.code(s[2][:10] + "...", language="text")
                # Botão individual para checar saldo sem estressar a rede
                if st.button(f"Saldo {s[1]}", key=f"btn_{s[0]}"):
                    saldo = W3.from_wei(W3.eth.get_balance(s[2]), 'ether')
                    st.write(f"⛽ {saldo:.3f} POL")

# --- MOTOR DE PREÇO ---
if "p" not in st.session_state: st.session_state.p = 98000.0
st.session_state.p += st.session_state.p * random.uniform(-0.004, 0.004)
st.sidebar.metric("PREÇO MERCADO", f"${st.session_state.p:,.2f}")

time.sleep(10) # Refresh lento para não tomar ban
st.rerun()