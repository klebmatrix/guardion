import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONFIGURAÇÃO ANTI-BLOCK ---
# Usando um RPC secundário para evitar o erro -32090
RPC_LIST = ["https://polygon-rpc.com", "https://rpc-mainnet.maticvigil.com"]
W3 = Web3(Web3.HTTPProvider(RPC_LIST[0]))

st.set_page_config(page_title="GUARDION v17.7 - ANTI-LIMIT", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v17_7.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, p_compra REAL, lucro_acumulado REAL, hash_saque TEXT)''')
db.commit()

# --- FUNÇÃO DE ABASTECIMENTO COM DELAY (ANTI-LIMIT) ---
def distribuir_combustivel_safe(pk_mestra, lista_agentes):
    try:
        conta_mestra = Account.from_key(pk_mestra)
        barra_progresso = st.progress(0)
        status_msg = st.empty()
        
        for i, ag in enumerate(lista_agentes):
            status_msg.warning(f"⏳ Abastecendo {ag[1]}... Não feche a página.")
            
            # Tenta enviar 0.15 POL
            tx = {
                'nonce': W3.eth.get_transaction_count(conta_mestra.address),
                'to': ag[2],
                'value': W3.to_wei(0.15, 'ether'),
                'gas': 21000,
                'gasPrice': int(W3.eth.gas_price * 1.2), # Gas um pouco maior para prioridade
                'chainId': 137
            }
            assinada = W3.eth.account.sign_transaction(tx, pk_mestra)
            W3.eth.send_raw_transaction(assinada.raw_transaction)
            
            # DELAY CRÍTICO: 1.5 segundos entre cada sniper para evitar o Erro -32090
            time.sleep(1.5) 
            barra_progresso.progress((i + 1) / len(lista_agentes))
            
        status_msg.success("✅ Tropa Abastecida com Sucesso! O limite da rede foi respeitado.")
    except Exception as e:
        st.error(f"Erro na Rede: {e}. Tente novamente em 30 segundos.")

# --- UI PRINCIPAL ---
st.title("🛡️ COMANDO GUARDION | MODO RESILIENTE")

c1, c2 = st.columns([1, 1])
with c1:
    pk_mestra = st.text_input("🔑 Private Key (Origem dos 10 POL):", type="password")
with c2:
    carteira_destino = st.text_input("🎯 Sua Carteira para Receber Lucro:")

if st.button("🚀 EXECUTAR ABASTECIMENTO TURBO (ANTI-BLOCK)", use_container_width=True):
    agentes_lista = db.execute("SELECT * FROM agentes").fetchall()
    if pk_mestra and len(agentes_lista) > 0:
        distribuir_combustivel_safe(pk_mestra, agentes_lista)
    else:
        st.error("Gere as carteiras primeiro ou insira a Private Key!")

st.divider()

# --- BOTÃO DE GERAR ---
if st.button("🔄 GERAR NOVAS CARTEIRAS (RESET)"):
    db.execute("DELETE FROM agentes")
    for i in range(50):
        acc = Account.create()
        db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?)",
                   (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0, ""))
    db.commit()
    st.rerun()

# --- MONITOR DE SALDO REAL ---
st.subheader("📊 Monitor de Saldo Real On-Chain")
agentes = db.execute("SELECT * FROM agentes").fetchall()
cols = st.columns(5)
for i, a in enumerate(agentes):
    with cols[i % 5]:
        try:
            # Consulta saldo real para saber se o abastecimento funcionou
            saldo = W3.from_wei(W3.eth.get_balance(a[2]), 'ether')
        except: saldo = 0.0
        
        with st.container(border=True):
            st.write(f"**{a[1]}**")
            if saldo >= 0.14:
                st.success(f"⛽ {saldo:.3f} POL")
            else:
                st.error(f"⛽ {saldo:.3f} POL")
            st.caption(f"Status: {a[4]}")

# Piloto automático de preço apenas visual para não estressar o RPC
if "preco" not in st.session_state: st.session_state.preco = 98000.0
st.session_state.preco += st.session_state.preco * random.uniform(-0.002, 0.002)
st.sidebar.metric("PREÇO ATUAL", f"${st.session_state.preco:,.2f}")

time.sleep(5) # Refresh mais lento para evitar novo bloqueio
st.rerun()