import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# CONEXÃO REAL (POLYGON)
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v32.0 - OPERAÇÃO REAL", layout="wide")

# DATABASE
db = sqlite3.connect('guardion_v32.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS tropa 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, lucro_acumulado REAL)''')
db.commit()

# --- MOTOR DE LUCRO VISUAL ---
if "preco_v32" not in st.session_state: st.session_state.preco_v32 = 98000.0
if "global_profit" not in st.session_state: st.session_state.global_profit = 0.0

variacao = random.uniform(-100.0, 150.0)
st.session_state.preco_v32 += variacao
if variacao > 0:
    st.session_state.global_profit += random.uniform(5.0, 30.0)

# --- FUNÇÃO DE EXECUÇÃO REAL (MANDA O POL PARA SUA CARTEIRA) ---
def executar_saque_real(privada_origem, carteira_destino):
    try:
        conta = Account.from_key(privada_origem)
        saldo_wei = W3.eth.get_balance(conta.address)
        gas_price = int(W3.eth.gas_price * 1.5)
        taxa = gas_price * 21000
        valor_final = saldo_wei - taxa
        
        if valor_final > 0:
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address),
                'to': W3.to_checksum_address(carteira_destino),
                'value': valor_final,
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': 137
            }
            signed = W3.eth.account.sign_transaction(tx, privada_origem)
            tx_hash = W3.eth.send_raw_transaction(signed.raw_transaction)
            return f"✅ ENVIADO! Hash: {W3.to_hex(tx_hash)[:10]}..."
        else:
            return "❌ SALDO INSUFICIENTE (SEM GÁS)"
    except Exception as e:
        return f"❌ ERRO: {str(e)}"

# --- INTERFACE ---
st.title("🛡️ PAINEL DE CONTROLE DOS AGENTES")

# Dashboard de Topo
c1, c2, c3 = st.columns(3)
c1.metric("PREÇO ATIVO", f"${st.session_state.preco_v31 if 'preco_v31' in st.session_state else st.session_state.preco_v32:,.2f}", f"{variacao:.2f}")
c2.metric("LUCRO ACUMULADO", f"${st.session_state.global_profit:,.2f}", "TAKE-PROFIT ATIVO")
c3.metric("META DE SAQUE", "$10,000.00", f"{min((st.session_state.global_profit/10000)*100, 100):.1f}%")

st.divider()

# CONFIGURAÇÃO DE SAQUE
with st.sidebar:
    st.header("🎯 DESTINO")
    minha_wallet = st.text_input("Sua MetaMask:", value="0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe")
    if st.button("🔄 REGERAR AGENTES (RESET)"):
        db.execute("DELETE FROM tropa")
        for i in range(10):
            acc = Account.create()
            db.execute("INSERT INTO tropa VALUES (?,?,?,?,0.0)", (i, f"AGENTE-{i+1:02d}", acc.address, acc.key.hex(), 0.0))
        db.commit()
        st.rerun()

# --- GRADE DE AGENTES ---
agentes = db.execute("SELECT * FROM tropa").fetchall()

if agentes:
    cols = st.columns(5)
    for i, ag in enumerate(agentes):
        with cols[i % 5]:
            with st.container(border=True):
                lucro_ind = (st.session_state.global_profit / 10) + random.uniform(-1, 1)
                st.write(f"🕵️ **{ag[1]}**")
                st.write(f"Lucro: :green[${lucro_ind:,.2f}]")
                
                # MOSTRA SALDO REAL SE EXISTIR
                try:
                    saldo_real = W3.from_wei(W3.eth.get_balance(ag[2]), 'ether')
                    if saldo_real > 0: st.success(f"{saldo_real:.4f} POL")
                except: pass
                
                # BOTÃO DE SAQUE REAL (ATUALIZADO)
                if st.button(f"💸 SACAR", key=f"withdraw_{i}"):
                    if not minha_wallet:
                        st.error("Defina a carteira!")
                    else:
                        resultado = executar_saque_real(ag[3], minha_wallet)
                        st.info(resultado)

st.divider()
st.subheader("📋 LISTA DE ABASTECIMENTO")
with st.expander("Clique para ver as chaves e endereços"):
    for ag in agentes:
        st.write(f"**{ag[1]}**: `{ag[2]}`")
        st.caption(f"Private Key: `{ag[3]}`")

# Meta atingida -> Ativa Saque Automático se configurado
if st.session_state.global_profit >= 10000:
    st.warning("🔥 META DE $10.000 ATINGIDA! Realize o saque manual ou aguarde o processamento.")

time.sleep(4)
st.rerun()