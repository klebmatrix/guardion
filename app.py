import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v12.9", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"
EXPLORER_URL = "https://polygonscan.com/tx/"

# --- LOGIN SEGURO ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.9")
    senha = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- DB & ESTRUTURA ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)
try: db.execute("ALTER TABLE agentes_v6 ADD COLUMN last_hash TEXT")
except: pass
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT, last_hash TEXT)''')
db.commit()

# --- MOTOR DE PREÇO (RESILIENTE) ---
def pegar_preco():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try: 
        return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3, headers=headers).json()['price'])
    except:
        try: return float(requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()['bitcoin']['usd'])
        except: return None

# --- FUNÇÃO: CÁLCULO E DIVISÃO AUTOMÁTICA DE POL ---
def auto_dividir_pol(pk_mestra):
    w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
    if not w3.is_connected(): return st.error("Erro RPC")
    
    mestra = Account.from_key(pk_mestra)
    saldo_wei = w3.eth.get_balance(mestra.address)
    saldo_pol = float(w3.from_wei(saldo_wei, 'ether'))
    
    # Lógica: Mantém 0.5 POL na mestra e divide o resto por 50
    reserva = 0.5
    if saldo_pol <= reserva:
        return st.error(f"Saldo insuficiente! Você tem apenas {saldo_pol:.4f} POL.")
    
    valor_cada = (saldo_pol - reserva) / 50
    st.warning(f"🚀 Enviando {valor_cada:.4f} POL para cada sniper...")
    
    agentes = db.execute("SELECT endereco, nome FROM agentes_v6").fetchall()
    barra = st.progress(0)
    for i, (end, nome) in enumerate(agentes):
        try:
            tx = {
                'nonce': w3.eth.get_transaction_count(mestra.address),
                'to': end,
                'value': w3.to_wei(valor_cada, 'ether'),
                'gas': 21000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 137
            }
            assinado = w3.eth.account.sign_transaction(tx, pk_mestra)
            tx_hash = w3.eth.send_raw_transaction(assinado.raw_transaction)
            db.execute("UPDATE agentes_v6 SET last_hash=?, ultima_acao='ABASTECIDO' WHERE endereco=?", (tx_hash.hex(), end))
            db.commit()
            barra.progress((i + 1) / 50)
            time.sleep(0.1) # Proteção contra rate limit
        except Exception as e:
            st.error(f"Erro no {nome}: {e}")
            break
    st.success("⛽ Logística concluída!")

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v12.9")
btc = pegar_preco()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    
    with st.sidebar:
        st.header("⚙️ COMANDO CENTRAL")
        if "pk_gas" not in st.session_state: st.session_state.pk_gas = ""
        st.session_state.pk_gas = st.text_input("Sua PK Mestra:", value=st.session_state.pk_gas, type="password")
        
        tp = st.slider("Take Profit (%)", 0.1, 5.0, 1.5)
        
        if st.button("🚀 REINICIAR 50 SNIPERS"):
            db.execute("DELETE FROM agentes_v6")
            for i in range(50):
                acc = Account.create()
                db.execute("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao, last_hash) VALUES (?,?,?,?,?,?,?,?)",
                           (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), btc - (i * 150), "VIGILANCIA", 0.0, "Pronto", ""))
            db.commit()
            st.rerun()
            
        st.divider()
        st.header("⛽ LOGÍSTICA")
        if st.button("💸 AUTO-DIVIDIR SALDO POL"):
            if st.session_state.pk_gas: auto_dividir_pol(st.session_state.pk_gas)
            else: st.warning("Insira a PK Mestra!")

    # Motor de Trade (Take Profit Ativo Infinito)
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    for ag in agentes:
        id_ag, nome, _, _, alvo, status, p_compra, _, _ = ag
        if btc <= alvo and status == "VIGILANCIA":
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, last_hash='Aguardando...' WHERE id=?", (btc, id_ag))
            db.commit()
        elif status == "COMPRADO" and btc >= p_compra * (1 + (tp/100)):
            db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, ultima_acao='TP Reset' WHERE id=?", (id_ag,))
            db.commit()

    # --- TABS ---
    tab1, tab2 = st.tabs(["🎯 Monitor", "📜 Histórico On-Chain"])
    with tab1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.caption(f"S: {a[5]}")

    with tab2:
        st.subheader("🕵️ Histórico de Hashes")
        df = pd.DataFrame(agentes, columns=['ID', 'Nome', 'End', 'Key', 'Alvo', 'Status', 'P.Compra', 'Ação', 'Hash'])
        for _, row in df[df['Hash'] != ""].iterrows():
            c1, c2 = st.columns([4, 1])
            c1.code(f"{row['Nome']} | {row['Hash']}")
            if "0x" in str(row['Hash']):
                c2.link_button("Explorer", f"{EXPLORER_URL}{row['Hash']}")
            st.divider()

else:
    st.error("⚠️ SEM SINAL DE REDE.")
    time.sleep(5)
    st.rerun()

time.sleep(15)
st.rerun()