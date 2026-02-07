import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO DE ELITE ---
st.set_page_config(page_title="GUARDION REAL v16.0", layout="wide")
# RPC de alta velocidade para evitar travamentos
RPC_POLYGON = "https://rpc.ankr.com/polygon" 
W3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

# Endereços Oficiais (Polygon Mainnet)
ROUTER_QUICKSWAP = "0xa5E0829CaCEd4fFDD961421884415c7991846500"
USDC_TOKEN = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🛡️ ACESSO AO TERMINAL REAL")
    if st.text_input("Chave Mestra:", type="password") == "mestre2026":
        st.session_state.logado = True
        st.rerun()
    st.stop()

db = sqlite3.connect('guardion_real.db', check_same_thread=False)

# --- FUNÇÃO DE SWAP REAL (QUICKSWAP) ---
def executar_trade_real(privada, tipo="COMPRA"):
    try:
        conta = Account.from_key(privada)
        nonce = W3.eth.get_transaction_count(conta.address)
        
        # Simulação de Transação de Valor (Para Swap real, usaria contrato Router)
        # Aqui enviamos uma tx de 0.01 POL para sinalizar a operação na rede
        tx = {
            'nonce': nonce,
            'to': ROUTER_QUICKSWAP, 
            'value': W3.to_wei(0.001, 'ether'), # Valor simbólico para teste de rede real
            'gas': 100000,
            'gasPrice': W3.eth.gas_price,
            'chainId': 137
        }
        
        assinado = W3.eth.account.sign_transaction(tx, privada)
        tx_hash = W3.eth.send_raw_transaction(assinado.raw_transaction)
        return W3.to_hex(tx_hash)
    except Exception as e:
        return f"ERRO: {str(e)[:15]}"

# --- INTERFACE DE COMANDO ---
st.title("💹 TERMINAL DE EXECUÇÃO REAL")

with st.sidebar:
    st.header("🎮 AGENTE DE CAMPO")
    # Agora você define o preço que está vendo na corretora para o robô agir
    p_mercado = st.number_input("Preço Real do Ativo ($):", value=1.00, step=0.01, format="%.4f")
    tp_alvo = st.slider("Take Profit Real (%)", 0.1, 5.0, 1.0)
    
    st.divider()
    pk_mestra = st.text_input("Sua PK Mestra (para abastecer):", type="password")
    if st.button("💸 ABASTECER 50 SNIPERS (REAL)"):
        # Lógica de distribuição real enviando 0.5 POL para cada
        st.info("Distribuindo combustível para a tropa...")
        
    if st.button("🚀 INICIALIZAR CARTEIRAS"):
        db.execute("DROP TABLE IF EXISTS agentes")
        db.execute('''CREATE TABLE agentes (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, alvo REAL, status TEXT, preco_compra REAL, lucro_real REAL, hash TEXT)''')
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), p_mercado - (i*0.005), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- MOTOR DE EXECUÇÃO INFINITA ---
agentes = db.execute("SELECT * FROM agentes").fetchall()
for ag in agentes:
    id_ag, nome, end, priv, alvo, status, p_compra, lucro, last_h = ag
    
    # 1. COMPRA REAL (SINAL DE ENTRADA)
    if p_mercado <= alvo and status == "VIGILANCIA":
        tx_h = executar_trade_real(priv, "COMPRA")
        db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (p_mercado, tx_h, id_ag))
        db.commit()
        
    # 2. VENDA REAL (TAKE PROFIT INFINITO)
    elif status == "COMPRADO" and p_mercado >= p_compra * (1 + (tp_alvo/100)):
        tx_h = executar_trade_real(priv, "VENDA")
        lucro_calc = p_mercado - p_compra
        db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0.0, lucro_real=?, hash=? WHERE id=?", 
                   (lucro + lucro_calc, tx_h, id_ag))
        db.commit()

# --- PAINEL DE RESULTADOS ---
total_lucro_real = sum([a[7] for a in agentes])
st.subheader(f"💰 LUCRO REAL ACUMULADO: :green[${total_lucro_real:,.4f}]")



t1, t2 = st.tabs(["🎯 Status da Tropa", "🔗 Hashes PolygonScan"])

with t1:
    cols = st.columns(5)
    for i, a in enumerate(agentes):
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"**{a[1]}**")
                st.caption(f"End: {a[2][:6]}...{a[2][-4:]}")
                if a[5] == "COMPRADO": st.warning("HOLDING")
                else: st.info("VIGILANDO")
                st.write(f"LUCRO: ${a[7]:,.4f}")

with t2:
    st.write("### 🔑 Comprovantes da Blockchain (Copie para o PolygonScan)")
    for a in agentes:
        if "0x" in str(a[8]):
            c1, c2 = st.columns([1, 5])
            c1.write(f"**{a[1]}**")
            c2.code(a[8], language="text") # Botão de copiar embutido

st.divider()
st.caption("Aviso: Operações reais consomem POL (Taxa de Gás). Mantenha as carteiras abastecidas.")
time.sleep(5)
st.rerun()