import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- CONFIGURAÇÃO DE REDE ---
st.set_page_config(page_title="GUARDION OMNI v11.1", layout="wide")
RPC_URL = "https://polygon-rpc.com" 
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- BANCO DE DADOS (V3 - ESTÁVEL) ---
def init_db():
    conn = sqlite3.connect('guardion_v3.db', check_same_thread=False)
    # Tabela expandida para incluir lucro e preço de compra
    conn.execute('''CREATE TABLE IF NOT EXISTS agentes 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- INTERFACE LATERAL ---
with st.sidebar:
    st.header("🔐 ACESSO MESTRE")
    pk_input = st.text_input("Sua PK_01 Conectada:", type="password", key="pk_main")
    
    PK_MESTRE = None
    if pk_input:
        try:
            pk_limpa = pk_input.strip().replace('"', '').replace("'", "")
            if not pk_limpa.startswith("0x") and len(pk_limpa) == 64: pk_limpa = "0x" + pk_limpa
            acc_mestre = Account.from_key(pk_limpa)
            PK_MESTRE = pk_limpa
            st.success(f"✅ MESTRE ONLINE")
        except: st.error("❌ Chave Inválida")

    st.divider()
    st.header("⚙️ AJUSTES DE COMBATE")
    p_topo = st.number_input("Preço Inicial (BTC):", value=102500.0)
    distancia = st.number_input("Distância Grid ($):", value=200.0)
    lucro_desejado = st.number_input("Lucro para Venda ($):", value=500.0)
    
    if st.button("🚀 REINICIAR BATALHÃO (25)"):
        if not PK_MESTRE: st.warning("Conecte a PK!")
        else:
            db.execute("DELETE FROM agentes")
            novos = []
            for i in range(25):
                acc = Account.create()
                alvo = p_topo - (i * distancia)
                novos.append((f"SNIPER-{i+1:02d}", acc.address, acc.key.hex(), alvo, "VIGILANCIA", 0.0, "Aguardando"))
            db.executemany("INSERT INTO agentes (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)", novos)
            db.commit()
            st.rerun()

# --- MOTOR DE EXECUÇÃO ---
def get_btc_price():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price'])
    except: return 0.0

def abastecer_agente(addr_agente):
    if not PK_MESTRE: return
    try:
        saldo_wei = w3.eth.get_balance(addr_agente)
        if saldo_wei < w3.to_wei(0.1, 'ether'):
            acc_m = Account.from_key(PK_MESTRE)
            tx = {
                'nonce': w3.eth.get_transaction_count(acc_m.address),
                'to': addr_agente, 'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            st.toast(f"⛽ Gas enviado para {addr_agente[:6]}")
    except: pass

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v11.1")
btc_atual = get_btc_price()

c1, c2, c3 = st.columns(3)
c1.metric("BTC ATUAL", f"${btc_atual:,.2f}")
c2.metric("LUCRO ALVO", f"+ ${lucro_desejado}")
c3.metric("STATUS", "OPERACIONAL" if btc_atual > 0 else "OFFLINE")

st.divider()

agentes = db.execute("SELECT * FROM agentes").fetchall()
if agentes:
    cols = st.columns(5)
    for idx, ag in enumerate(agentes):
        id_banco, nome, endereco, privada, alvo, status, p_compra, acao = ag
        with cols[idx % 5]:
            with st.container(border=True):
                time.sleep(0.02) # Anti-ban RPC
                try: saldo = round(w3.from_wei(w3.eth.get_balance(endereco), 'ether'), 2)
                except: saldo = 0.0
                
                # --- LÓGICA DE COMPRA/VENDA ---
                cor_status = "white"
                if status == "VIGILANCIA":
                    if btc_atual <= alvo and btc_atual > 0:
                        db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, ultima_acao='ORDEM COMPRA' WHERE id=?", (btc_atual, id_banco))
                        db.commit()
                        st.rerun()
                elif status == "COMPRADO":
                    cor_status = "#00FF00" # Verde para quando está posicionado
                    if btc_atual >= (p_compra + lucro_desejado):
                        db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0, ultima_acao='LUCRO REALIZADO' WHERE id=?", (id_banco,))
                        db.commit()
                        st.rerun()

                st.markdown(f"<p style='color:{cor_status}; font-weight:bold;'>{nome}</p>", unsafe_allow_html=True)
                st.write(f"⛽ {saldo} POL")
                st.caption(f"🎯 Alvo: ${alvo:,.0f}")
                if status == "COMPRADO":
                    st.success(f"Compra: ${p_compra:,.0f}")
                
                if PK_MESTRE and saldo < 0.1:
                    abastecer_agente(endereco)
else:
    st.info("Aguardando ativação do batalhão.")

time.sleep(45)
st.rerun()