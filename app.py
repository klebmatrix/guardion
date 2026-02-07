import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v12.8", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"
EXPLORER_URL = "https://polygonscan.com/tx/"

# --- LOGIN SEGURO ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.8")
    senha = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- DB COM SUPORTE A HASH ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)
try: db.execute("ALTER TABLE agentes_v6 ADD COLUMN last_hash TEXT")
except: pass
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT, last_hash TEXT)''')
db.commit()

# --- FUNÇÃO: DIVIDIR POL (GÁS) ---
def distribuir_pol(pk_mestra, valor_cada):
    w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
    if not w3.is_connected():
        st.error("Erro de conexão RPC")
        return
    
    conta_mestra = Account.from_key(pk_mestra)
    agentes = db.execute("SELECT endereco, nome FROM agentes_v6").fetchall()
    
    st.info(f"🚀 Iniciando logística de {valor_cada} POL para {len(agentes)} snipers...")
    barra = st.progress(0)
    
    for i, (end, nome) in enumerate(agentes):
        try:
            tx = {
                'nonce': w3.eth.get_transaction_count(conta_mestra.address),
                'to': end,
                'value': w3.to_wei(valor_cada, 'ether'),
                'gas': 21000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, pk_mestra)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            barra.progress((i + 1) / len(agentes))
        except Exception as e:
            st.error(f"Falha no {nome}: {e}")
            break
    st.success("⛽ Logística concluída! Todos os snipers estão armados.")

# --- MOTOR DE PREÇO ---
def pegar_preco():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()['price'])
    except: return None

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v12.8")
btc = pegar_preco()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    
    with st.sidebar:
        st.header("⚙️ COMANDO CENTRAL")
        if "pk_gas" not in st.session_state: st.session_state.pk_gas = ""
        st.session_state.pk_gas = st.text_input("PK Mestra (POL):", value=st.session_state.pk_gas, type="password")
        
        tp = st.slider("Take Profit (%)", 0.1, 5.0, 2.0)
        
        if st.button("🚀 REGERAR 50 SNIPERS"):
            db.execute("DELETE FROM agentes_v6")
            for i in range(50):
                acc = Account.create()
                db.execute("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao, last_hash) VALUES (?,?,?,?,?,?,?,?)",
                           (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), btc - (i * 100), "VIGILANCIA", 0.0, "Pronto", ""))
            db.commit()
            st.rerun()
            
        st.divider()
        st.header("⛽ LOGÍSTICA DE GÁS")
        valor_pol = st.number_input("POL por Sniper:", value=0.1)
        if st.button("💸 DIVIDIR POL AGORA"):
            if st.session_state.pk_gas: distribuir_pol(st.session_state.pk_gas, valor_pol)
            else: st.warning("Insira a PK Mestra!")

    # Lógica de Trade (Take Profit Ativo Infinito)
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    for ag in agentes:
        id_ag, nome, _, _, alvo, status, p_compra, _, _ = ag
        if btc <= alvo and status == "VIGILANCIA":
            # Aqui entraria o Swap Web3 real
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, last_hash='Aguardando TX...' WHERE id=?", (btc, id_ag))
            db.commit()
        elif status == "COMPRADO" and btc >= p_compra * (1 + (tp/100)):
            db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, ultima_acao='Reset Infinito' WHERE id=?", (id_ag,))
            db.commit()

    # --- TABS ---
    tab1, tab2 = st.tabs(["🎯 Monitor", "📜 Histórico On-Chain"])
    
    with tab1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.caption(f"Status: {a[5]}")

    with tab2:
        st.subheader("🕵️ Histórico de Transações Reais")
        df = pd.DataFrame(agentes, columns=['ID', 'Nome', 'End', 'Key', 'Alvo', 'Status', 'P.Compra', 'Ação', 'Hash'])
        df_hist = df[df['Hash'] != ""].copy()
        
        if not df_hist.empty:
            for _, row in df_hist.iterrows():
                c1, c2, c3 = st.columns([1, 4, 1])
                c1.write(f"**{row['Nome']}**")
                c2.code(row['Hash'])
                if "0x" in str(row['Hash']):
                    c3.link_button("Explorer", f"{EXPLORER_URL}{row['Hash']}")
                st.divider()
        else: st.info("Nenhuma transação registrada.")

else:
    st.error("Sem sinal de rede.")

time.sleep(20)
st.rerun()