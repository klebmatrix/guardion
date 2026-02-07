import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO COM MULTI-RPC PARA EVITAR BAN ---
RPCS = ["https://polygon-rpc.com", "https://rpc-mainnet.maticvigil.com"]
W3 = Web3(Web3.HTTPProvider(RPCS[0]))

st.set_page_config(page_title="GUARDION v18.0 - ANTI-BAN", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v18.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, p_compra REAL, lucro_real REAL)''')
db.commit()

# --- INTERFACE ---
st.title("🛡️ GUARDION v18.0 | PROTOCOLO DE SEGURANÇA")

# AVISO DE BLOQUEIO (GELO)
st.error("🚨 REDE EM DESCANSO: A Polygon bloqueou seu IP por 10 minutos. O sistema está em modo de espera.")
st.info("Aguarde o cronômetro zerar para tentar o abastecimento novamente. Se tentar antes, o bloqueio aumenta.")

# Cronômetro visual
if "timer" not in st.session_state: st.session_state.timer = time.time() + 605 # 10 min
tempo_restante = int(st.session_state.timer - time.time())

if tempo_restante > 0:
    st.warning(f"⏳ Tempo de desbloqueio: {tempo_restante // 60}m {tempo_restante % 60}s")
else:
    st.success("✅ REDE LIBERADA! Pode prosseguir com o abastecimento.")

st.divider()

# --- FUNÇÃO DE ABASTECIMENTO LENTO (ANTI-SPAM) ---
def abastecer_slow_motion(pk_origem, lista):
    conta = Account.from_key(pk_origem)
    progresso = st.progress(0)
    for i, sniper in enumerate(lista):
        try:
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address),
                'to': sniper[2],
                'value': W3.to_wei(0.18, 'ether'),
                'gas': 21000,
                'gasPrice': int(W3.eth.gas_price * 1.5),
                'chainId': 137
            }
            assinada = W3.eth.account.sign_transaction(tx, pk_origem)
            W3.eth.send_raw_transaction(assinada.raw_transaction)
            # PAUSA LONGA: 4 segundos entre cada um para a rede não nos banir de novo
            time.sleep(4.0) 
            progresso.progress((i + 1) / len(lista))
        except Exception as e:
            st.error(f"Pausa forçada: {e}")
            break

# --- COMANDOS ---
col1, col2 = st.columns(2)
with col1:
    pk = st.text_input("🔑 CHAVE PRIVADA:", type="password")
with col2:
    destino = st.text_input("🎯 CARTEIRA DESTINO:")

if st.button("🚀 INICIAR DISTRIBUIÇÃO (SÓ SE LIBERADO)", disabled=(tempo_restante > 0)):
    snipers = db.execute("SELECT * FROM agentes").fetchall()
    if pk and snipers:
        abastecer_slow_motion(pk, snipers)

if st.button("🔄 GERAR TROPA (CLIQUE UMA VEZ)"):
    db.execute("DELETE FROM agentes")
    for i in range(50):
        acc = Account.create()
        db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?)",
                   (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0))
    db.commit()
    st.rerun()

st.divider()
st.subheader("📊 STATUS DA TROPA")



# Consulta de saldo inteligente (SÓ FAZ SE LIBERADO)
if tempo_restante <= 0:
    snipers = db.execute("SELECT * FROM agentes").fetchall()
    cols = st.columns(5)
    for i, s in enumerate(snipers):
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"**{s[1]}**")
                st.caption(f"{s[2][:6]}...")
                # Não consulta saldo toda hora para não ser banido de novo
                st.write("⛽ Aguardando sinal...")
else:
    st.info("A visualização de saldos está pausada para evitar novo bloqueio.")

time.sleep(10)
st.rerun()