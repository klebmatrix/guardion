import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO ---
RPC_POLYGON = "https://polygon-rpc.com"
W3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

st.set_page_config(page_title="GUARDION OMNI v16.9", layout="wide")

# --- BANCO DE DADOS ---
db = sqlite3.connect('guardion_final_real.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, preco_compra REAL, lucro_acumulado REAL, last_hash TEXT)''')
db.commit()

# --- FUNÇÕES DE BLOCKCHAIN ---
def distribuir_gas(pk_mestra, enderecos_snipers):
    conta_mestra = Account.from_key(pk_mestra)
    for end in enderecos_snipers:
        try:
            tx = {
                'nonce': W3.eth.get_transaction_count(conta_mestra.address),
                'to': end,
                'value': W3.to_wei(0.2, 'ether'), # Envia 0.2 POL para cada sniper
                'gas': 21000,
                'gasPrice': W3.eth.gas_price,
                'chainId': 137
            }
            assinado = W3.eth.account.sign_transaction(tx, pk_mestra)
            W3.eth.send_raw_transaction(assinado.raw_transaction)
            time.sleep(0.2) # Evita erro de nonce
        except: pass

def sacar_lucro_real(privada_agente, carteira_destino):
    try:
        conta = Account.from_key(privada_agente)
        saldo = W3.eth.get_balance(conta.address)
        taxa = W3.eth.gas_price * 21000
        if saldo > taxa + W3.to_wei(0.01, 'ether'):
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address),
                'to': carteira_destino,
                'value': saldo - taxa,
                'gas': 21000,
                'gasPrice': W3.eth.gas_price,
                'chainId': 137
            }
            assinado = W3.eth.account.sign_transaction(tx, privada_agente)
            tx_h = W3.eth.send_raw_transaction(assinado.raw_transaction)
            return W3.to_hex(tx_h)
    except: return None

# --- UI ---
st.title("🛡️ COMMANDER OMNI | OPERAÇÃO REAL TOTAL")

if "p" not in st.session_state: st.session_state.p = 97000.0

with st.sidebar:
    st.header("⛽ COMBUSTÍVEL (GÁS)")
    pk_mestra = st.text_input("Sua Private Key (Para distribuir POL):", type="password")
    if st.button("🚀 ABASTECER 50 SNIPERS"):
        agentes = db.execute("SELECT endereco FROM agentes").fetchall()
        distribuir_gas(pk_mestra, [a[0] for a in agentes])
        st.success("Distribuição iniciada!")

    st.divider()
    st.header("💰 RETIRADA AUTOMÁTICA")
    carteira_saque = st.text_input("Sua Carteira Mestra (Destino):")
    tp_pct = st.slider("Take Profit (%)", 0.1, 2.0, 0.5)
    
    pilot_on = st.toggle("🚀 PILOTO AUTOMÁTICO", value=True)
    if st.button("🔄 REINICIAR TUDO"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- MOTOR ---
if pilot_on: st.session_state.p += st.session_state.p * random.uniform(-0.003, 0.003)

agentes = db.execute("SELECT * FROM agentes").fetchall()
for ag in agentes:
    id_ag, nome, end, priv, status, p_compra, lucro, h = ag
    
    # COMPRA
    if st.session_state.p <= 97000.0 and status == "VIGILANCIA":
        db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=? WHERE id=?", (st.session_state.p, id_ag))
    
    # VENDA + SAQUE REAL
    elif status == "COMPRADO" and st.session_state.p >= p_compra * (1 + (tp_pct/100)):
        tx_sucesso = None
        if carteira_saque.startswith("0x"):
            tx_sucesso = sacar_lucro_real(priv, carteira_saque)
        
        db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=?, last_hash=? WHERE id=?", 
                   (lucro + (st.session_state.p - p_compra), tx_sucesso if tx_sucesso else h, id_ag))
db.commit()

# --- DASHBOARD ---
st.metric("PREÇO ATUAL", f"${st.session_state.p:,.2f}")
st.subheader(f"💵 LUCRO TOTAL EM TRÂNSITO: :green[${sum([a[6] for a in agentes]):,.2f}]")



t1, t2 = st.tabs(["🎯 Monitor", "🔗 Comprovantes On-Chain"])
with t1:
    cols = st.columns(5)
    for i, a in enumerate(agentes):
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"**{a[1]}**")
                saldo_pol = W3.eth.get_balance(a[2])
                st.caption(f"Gás: {W3.from_wei(saldo_pol, 'ether'):.2f} POL")
                st.write(f"Lucro: ${a[6]:,.2f}")

with t2:
    for a in agentes:
        if a[7] and "0x" in str(a[7]):
            st.success(f"{a[1]} -> Saque Realizado! Hash: {a[7]}")

time.sleep(3)
st.rerun()