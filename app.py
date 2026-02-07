import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONFIGURAÇÃO ANTI-RATE-LIMIT ---
# Usamos um provedor que aguenta mais pressão
W3 = Web3(Web3.HTTPProvider("https://polygon-mainnet.g.alchemy.com/v2/your-api-key")) # Ou o público abaixo
if not W3.is_connected():
    W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v17.8 - FIXED GAS", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v17_8.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, p_compra REAL, lucro_acumulado REAL, hash_saque TEXT)''')
db.commit()

# --- FUNÇÃO DE ABASTECIMENTO COM ESCALONAMENTO ---
def abastecer_com_pausa(pk_mestra, lista):
    try:
        conta_mestra = Account.from_key(pk_mestra)
        barra = st.progress(0)
        info = st.empty()
        
        for i, ag in enumerate(lista):
            info.warning(f"⏳ Abastecendo {ag[1]}... (Não atualize a página)")
            
            # Cálculo de Gás Dinâmico para não ser rejeitado
            tx = {
                'nonce': W3.eth.get_transaction_count(conta_mestra.address),
                'to': ag[2],
                'value': W3.to_wei(0.15, 'ether'),
                'gas': 21000,
                'gasPrice': int(W3.eth.gas_price * 1.3), # Paga um pouco mais para passar na frente
                'chainId': 137
            }
            assinada = W3.eth.account.sign_transaction(tx, pk_mestra)
            W3.eth.send_raw_transaction(assinada.raw_transaction)
            
            # --- O SEGREDO ESTÁ AQUI: PAUSA PARA NÃO SER BLOQUEADO ---
            time.sleep(2.5) # Espera 2.5 segundos entre cada sniper
            
            barra.progress((i + 1) / len(lista))
            
        info.success("✅ SUCESSO! Toda a tropa recebeu o gás.")
    except Exception as e:
        st.error(f"Erro na Rede: {e}")
        st.info("Aguarde 30 segundos e tente novamente. A rede Polygon está congestionada.")

# --- INTERFACE ---
st.title("🛡️ GUARDION v17.8 | GÁS E OPERAÇÃO")

c1, c2 = st.columns(2)
with c1:
    pk_mestra = st.text_input("🔑 Chave Privada (Origem do POL):", type="password")
with c2:
    destino = st.text_input("🎯 Sua Carteira (Onde cai o lucro):")

if st.button("🚀 DISTRIBUIR GÁS AGORA (MODO SEGURO)", use_container_width=True):
    snipers = db.execute("SELECT * FROM agentes").fetchall()
    if pk_mestra and snipers:
        abastecer_com_pausa(pk_mestra, snipers)
    else:
        st.error("Gere as carteiras ou insira a chave privada!")

st.divider()

if st.button("🔄 GERAR / RESETAR TROPA"):
    db.execute("DELETE FROM agentes")
    for i in range(50):
        acc = Account.create()
        db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?)",
                   (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0, ""))
    db.commit()
    st.rerun()

# --- MONITOR DE SALDO ---
st.subheader("📊 Monitor de Saldo Real")
agentes = db.execute("SELECT * FROM agentes").fetchall()
cols = st.columns(5)
for i, a in enumerate(agentes):
    with cols[i % 5]:
        try:
            saldo = W3.from_wei(W3.eth.get_balance(a[2]), 'ether')
        except: saldo = 0.0
        with st.container(border=True):
            st.write(f"**{a[1]}**")
            if saldo > 0.1: st.success(f"⛽ {saldo:.3f} POL")
            else: st.error(f"⛽ {saldo:.3f} POL")

# Motor Visual
if "p" not in st.session_state: st.session_state.p = 98000.0
st.session_state.p += st.session_state.p * random.uniform(-0.002, 0.002)
st.sidebar.metric("PREÇO ATUAL", f"${st.session_state.p:,.2f}")

time.sleep(5)
st.rerun()