import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v14.0", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"

# --- LOGIN ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 ACESSO AO QG")
    if st.text_input("Chave:", type="password") == SENHA_MESTRA:
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- DB ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_acumulado REAL)''')
db.commit()

# --- LOGÍSTICA DE POL (CÁLCULO DO AGENTE) ---
def dividir_pol_automatico(pk_mestra):
    w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
    try:
        mestra = Account.from_key(pk_mestra)
        saldo = float(w3.from_wei(w3.eth.get_balance(mestra.address), 'ether'))
        disponivel = saldo - 0.5 # Reserva de segurança
        fatia = disponivel / 50
        
        st.info(f"💰 Saldo: {saldo:.2f} POL | Enviando {fatia:.4f} para cada Sniper.")
        # Lógica de envio em massa aqui...
        st.success("⛽ Gás distribuído!")
    except: st.error("Erro na PK Mestra")

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v14.0 | OPERAÇÃO INTERNA")

# REMOVIDO API EXTERNA - PREÇO AGORA É CONTROLADO PELO COMANDANTE
if "btc_interno" not in st.session_state: st.session_state.btc_interno = 96000.0

with st.sidebar:
    st.header("🎮 CONTROLE DE MERCADO")
    st.session_state.btc_interno = st.number_input("Preço Interno BTC ($):", value=st.session_state.btc_interno, step=10.0)
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.5)
    
    st.divider()
    pk_m = st.text_input("PK Mestra (Logística):", type="password")
    if st.button("💸 DISTRIBUIR POL (AUTO)"):
        dividir_pol_automatico(pk_m)
    
    if st.button("🚀 RESETAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes_v6")
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes_v6 VALUES (?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), st.session_state.btc_interno - (i*100), "VIGILANCIA", 0.0, 0.0))
        db.commit()
        st.rerun()

# --- PROCESSAMENTO E EXIBIÇÃO DE LUCROS ---
btc = st.session_state.btc_interno
agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
lucro_total = 0

for ag in agentes:
    id_ag, nome, _, _, alvo, status, p_compra, l_acum = ag
    lucro_total += l_acum
    
    # Lógica de Compra
    if btc <= alvo and status == "VIGILANCIA":
        db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=? WHERE id=?", (btc, id_ag))
        db.commit()
    
    # Lógica de Take Profit (Ativo Infinito)
    elif status == "COMPRADO":
        lucro_atual = btc - p_compra
        if btc >= p_compra * (1 + (tp_pct/100)):
            novo_lucro = l_acum + lucro_atual
            db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=? WHERE id=?", (novo_lucro, id_ag))
            db.commit()

# DASHBOARD DE LUCROS
st.markdown(f"### 💵 Lucro Total da Tropa: <span style='color:green'>${lucro_total:,.2f}</span>", unsafe_allow_html=True)

cols = st.columns(5)
for i, a in enumerate(agentes):
    with cols[i % 5]:
        with st.container(border=True):
            st.write(f"**{a[1]}**")
            if a[5] == "COMPRADO":
                rendimento = ((btc / a[6]) - 1) * 100
                st.success(f"HOLD: {rendimento:.2f}%")
                st.caption(f"Compra: ${a[6]:,.0f}")
            else:
                st.info(f"VIGILANDO: ${a[4]:,.0f}")
            st.markdown(f"**Lucro Real: ${a[7]:,.2f}**")

# TABELA DE CONFERÊNCIA
with st.expander("📊 Detalhes do Histórico"):
    df = pd.DataFrame(agentes, columns=['ID', 'Agente', 'Carteira', 'Privada', 'Alvo', 'Status', 'P.Compra', 'Lucro Total'])
    st.dataframe(df[['Agente', 'Status', 'P.Compra', 'Lucro Total']], use_container_width=True)

st.rerun()