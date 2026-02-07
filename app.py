import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random

# --- CONEXÃO TURBO POLYGON ---
RPC_POLYGON = "https://polygon-rpc.com"
W3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

st.set_page_config(page_title="GUARDION v17.2 - REAL SEND", layout="wide")

# --- BANCO DE DADOS ---
db = sqlite3.connect('guardion_real_final.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
            status TEXT, p_compra REAL, lucro_acumulado REAL, hash_saque TEXT)''')
db.commit()

# --- MOTOR DE SAQUE REAL (WEB3) ---
def executar_saque_blockchain(privada_agente, carteira_mestra):
    try:
        conta = Account.from_key(privada_agente)
        saldo_wei = W3.eth.get_balance(conta.address)
        gas_price = W3.eth.gas_price
        custo_gas = gas_price * 21000 # Custo padrão de transferência
        
        # SÓ ENVIA SE TIVER SALDO PARA PAGAR A TAXA DA REDE
        if saldo_wei > custo_gas + W3.to_wei(0.001, 'ether'):
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address),
                'to': carteira_mestra,
                'value': saldo_wei - custo_gas,
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': 137
            }
            assinado = W3.eth.account.sign_transaction(tx, privada_agente)
            tx_hash = W3.eth.send_raw_transaction(assinado.raw_transaction)
            return W3.to_hex(tx_hash)
        else:
            return "SEM_GAS"
    except Exception as e:
        return f"ERRO_REDE"

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI | VERIFICAÇÃO DE RECEBIMENTO")

with st.sidebar:
    st.header("💰 CONFIGURAÇÃO DE SAQUE")
    sua_carteira = st.text_input("Sua Carteira Mestra (Destino):", placeholder="0x...")
    
    st.divider()
    pilot_on = st.toggle("🚀 PILOTO AUTOMÁTICO", value=True)
    
    if st.button("🔄 REINICIAR E GERAR NOVAS CARTEIRAS"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- MOTOR DE PREÇO ---
if "preco" not in st.session_state: st.session_state.preco = 98000.0
if pilot_on: st.session_state.preco += st.session_state.preco * random.uniform(-0.005, 0.005)

# --- PROCESSAMENTO ---
agentes = db.execute("SELECT * FROM agentes").fetchall()
for ag in agentes:
    id_a, nome, end, priv, status, p_c, lucro, h = ag
    
    # Simula Compra
    if st.session_state.preco <= 98000.0 and status == "VIGILANCIA":
        db.execute("UPDATE agentes SET status='COMPRADO', p_compra=? WHERE id=?", (st.session_state.preco, id_a))
    
    # Venda e TENTATIVA DE SAQUE REAL
    elif status == "COMPRADO" and st.session_state.preco >= p_c * 1.005:
        res_saque = "SIMULADO"
        if sua_carteira.startswith("0x"):
            res_saque = executar_saque_blockchain(priv, sua_carteira)
        
        db.execute("UPDATE agentes SET status='VIGILANCIA', p_compra=0.0, lucro_acumulado=?, hash_saque=? WHERE id=?", 
                   (lucro + (st.session_state.preco - p_c), res_saque, id_a))
db.commit()

# --- DASHBOARD DE GÁS E RECEBIMENTO ---
st.metric("PREÇO ATUAL", f"${st.session_state.preco:,.2f}")

st.subheader("📊 Monitor de Combustível (POL) dos Snipers")
st.caption("Se o Gás estiver 0.00, nada chegará na sua carteira. Envie 0.5 POL para os endereços abaixo.")

cols = st.columns(5)
for i, a in enumerate(agentes):
    with cols[i % 5]:
        with st.container(border=True):
            # Consulta saldo real na Blockchain
            try:
                saldo_real = W3.eth.get_balance(a[2])
                gas_status = W3.from_wei(saldo_real, 'ether')
            except: gas_status = 0
            
            st.write(f"**{a[1]}**")
            if gas_status > 0:
                st.success(f"⛽ {gas_status:.4f} POL")
            else:
                st.error("⛽ SEM GÁS")
                
            if "0x" in str(a[7]):
                st.info("✅ ENVIADO!")
            elif a[7] == "SEM_GAS":
                st.warning("⚠️ TRAVADO (SEM GÁS)")

time.sleep(2)
st.rerun()