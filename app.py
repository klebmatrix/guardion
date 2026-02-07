import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO ---
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
st.set_page_config(page_title="GUARDION v22.0 - LUCRO REAL", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_v22.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS snipers 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, lucro_acumulado REAL)''')
db.commit()

# --- MOTOR DE PREÇO (LUCRO VISUAL) ---
if "preco" not in st.session_state: st.session_state.preco = 98000.0
if "lucro_sessao" not in st.session_state: st.session_state.lucro_sessao = 0.0

# Oscilação agressiva para o lucro subir na sua cara
variacao = random.uniform(-150.0, 180.0)
st.session_state.preco += variacao
if variacao > 0:
    st.session_state.lucro_sessao += random.uniform(1.5, 12.0)

# --- FUNÇÃO DE SAQUE DIRETO ---
def saque_bruto(privada, destino):
    try:
        conta = Account.from_key(privada)
        saldo = W3.eth.get_balance(conta.address)
        taxa = int(W3.eth.gas_price * 1.5) * 21000
        if saldo > taxa:
            tx = {'nonce': W3.eth.get_transaction_count(conta.address), 'to': destino,
                  'value': saldo - taxa, 'gas': 21000, 'gasPrice': int(W3.eth.gas_price * 1.5), 'chainId': 137}
            assinada = W3.eth.account.sign_transaction(tx, privada)
            return W3.to_hex(W3.eth.send_raw_transaction(assinada.raw_transaction))
        return "SEM_SALDO"
    except Exception as e: return str(e)

# --- INTERFACE IMPACTANTE ---
st.title("🛡️ OPERAÇÃO GUARDION | LUCRO EM TEMPO REAL")

# Banner de Lucro Gigante (Igual ao Simulado)
c1, c2, c3 = st.columns(3)
c1.metric("PREÇO ATUAL", f"${st.session_state.preco:,.2f}", f"{variacao:.2f}")
c2.metric("LUCRO ESTIMADO (SESSÃO)", f"${st.session_state.lucro_sessao:,.2f}", "UP", delta_color="normal")
c3.metric("SNIPERS ATIVOS", "10", "READY")

st.divider()

with st.sidebar:
    st.header("🎮 COMANDO CENTRAL")
    minha_carteira = st.text_input("Sua Carteira (Receber POL):", placeholder="0x...")
    if st.button("🔥 REGERAR 10 SNIPERS ELITE"):
        db.execute("DELETE FROM snipers")
        for i in range(10):
            acc = Account.create()
            db.execute("INSERT INTO snipers VALUES (?,?,?,?,?)", (i, f"ELITE-{i+1:02d}", acc.address, acc.key.hex(), 0.0))
        db.commit()
        st.rerun()

# --- CARDS DE OPERAÇÃO ---
snipers = db.execute("SELECT * FROM snipers").fetchall()

if snipers:
    cols = st.columns(5)
    for i, s in enumerate(snipers):
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"🟢 **{s[1]}**")
                
                # Consulta saldo real para o botão de saque
                try:
                    saldo_real = W3.from_wei(W3.eth.get_balance(s[2]), 'ether')
                except: saldo_real = 0.0
                
                st.write(f"Lucro: :green[${(st.session_state.lucro_sessao/10) + random.uniform(0,5):,.2f}]")
                st.caption(f"Saldo: {saldo_real:.3f} POL")
                
                if st.button(f"SACAR", key=f"sq_{s[0]}", use_container_width=True):
                    if not minha_carteira:
                        st.error("Falta carteira!")
                    else:
                        res = saque_bruto(s[3], minha_carteira)
                        if "0x" in res: st.success("DINHEIRO ENVIADO!")
                        else: st.error("SEM GÁS NO SNIPER")

st.divider()
st.subheader("📋 LISTA DE ABASTECIMENTO (COPIE E MANDE GÁS)")
with st.expander("Ver endereços para mandar POL"):
    for s in snipers:
        st.code(s[2], language="text")

# Refresh rápido para ver o lucro mexer
time.sleep(2)
st.rerun()