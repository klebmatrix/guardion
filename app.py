import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v14.8", layout="wide")

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 QG GUARDION - MODO AUTO-PILOT")
    if st.text_input("Chave do QG:", type="password") == st.secrets.get("SECRET_KEY", "mestre2026"):
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- DB & ESTRUTURA ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

def reset_full():
    db.execute("DROP TABLE IF EXISTS agentes_v6")
    db.execute('''CREATE TABLE agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, ativo TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_acumulado REAL, ultimo_hash TEXT)''')
    db.commit()

# --- MOTOR DO AUTO-PILOT (SIMULADOR DE OSCILAÇÃO) ---
if "btc_auto" not in st.session_state: st.session_state.btc_auto = 95000.0
if "auto_pilot" not in st.session_state: st.session_state.auto_pilot = False

# Simula variação de -0.5% a +0.5% a cada ciclo
if st.session_state.auto_pilot:
    variacao = st.session_state.btc_auto * random.uniform(-0.005, 0.005)
    st.session_state.btc_auto += variacao

# --- UI COMANDO ---
st.title("🛡️ COMMANDER OMNI | MODO AUTO-PILOT")

with st.sidebar:
    st.header("🎮 PILOTO AUTOMÁTICO")
    st.session_state.auto_pilot = st.toggle("ATIVAR AUTO-PILOT", value=st.session_state.auto_pilot)
    
    st.divider()
    # Ativo Selecionado
    moeda = st.selectbox("Monitorar Ativo:", ["BTC", "ETH", "POL", "SOL"])
    st.metric("Preço Atual (Simulado)", f"${st.session_state.btc_auto:,.2f}")
    
    tp_pct = st.slider("Take Profit (%)", 0.1, 3.0, 0.5)
    
    if st.button("🚀 RESET & ALINHAR GRID"):
        reset_full()
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes_v6 VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", moeda, acc.address, acc.key.hex(), st.session_state.btc_auto * (1 - (i*0.001)), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- PROCESSAMENTO DE TRADE INFINITO ---
try:
    btc = st.session_state.btc_auto
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    
    for ag in agentes:
        id_ag, nome, ativo_ag, end, priv, alvo, status, p_compra, l_acum, u_hash = ag
        
        # Lógica de Compra Automática
        if btc <= alvo and status == "VIGILANCIA":
            h = f"0x{int(time.time())}AUTO_B_{id_ag}"
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultimo_hash=? WHERE id=?", (btc, h, id_ag))
        
        # Lógica de Venda Automática (Reset Infinito)
        elif status == "COMPRADO" and btc >= p_compra * (1 + (tp_pct/100)):
            lucro = btc - p_compra
            h = f"0x{int(time.time())}AUTO_S_{id_ag}"
            db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=?, ultimo_hash=? WHERE id=?", 
                       (l_acum + lucro, h, id_ag))
    db.commit()

    # --- DASHBOARD ---
    total_lucro = sum([a[8] for a in agentes])
    st.success(f"### 💵 LUCRO TOTAL ACUMULADO NO AUTO-PILOT: ${total_lucro:,.2f}")

    tab1, tab2 = st.tabs(["🎯 Monitor em Tempo Real", "📜 Hashes de Auditoria"])

    with tab1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.write(f"Lucro: :green[${a[8]:,.2f}]")
                    if a[6] == "COMPRADO": st.warning("HOLDING")
                    else: st.info("VIGILANDO")

    with tab2:
        st.subheader("🔑 Hashes de Movimentação (Copiar)")
        df_h = pd.DataFrame(agentes, columns=['ID','Nome','Ativo','End','Key','Alvo','Status','P.Compra','Lucro','Hash'])
        for _, row in df_h[df_h['Hash'] != ""].iterrows():
            c1, c2 = st.columns([1, 4])
            c1.write(f"**{row['Nome']}**")
            c2.code(row['Hash'], language="text") # Botão de copiar embutido
            st.divider()

except Exception as e:
    st.error(f"Erro no Motor: {e}. Clique em RESET no menu lateral.")

# Refresh rápido para ver a oscilação acontecer
time.sleep(3)
st.rerun()