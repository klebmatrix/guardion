import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v14.3", layout="wide")
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

# --- DB COM COLUNA DE HASH ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

def reset_db_completo():
    db.execute("DROP TABLE IF EXISTS agentes_v6")
    db.execute('''CREATE TABLE agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_acumulado REAL, ultimo_hash TEXT)''')
    db.commit()

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI v14.3 | RASTREAMENTO")

if "preco_base" not in st.session_state: st.session_state.preco_base = 97000.0

with st.sidebar:
    st.header("🎮 COMANDO")
    st.session_state.preco_base = st.number_input("Preço Interno ($):", value=st.session_state.preco_base, step=100.0)
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.2)
    
    st.divider()
    if st.button("🚀 REINICIAR E CORRIGIR ESTRUTURA"):
        reset_db_completo()
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes_v6 VALUES (?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), st.session_state.preco_base - (i*150), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- PROCESSAMENTO ---
btc = st.session_state.preco_base
try:
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    lucro_tropa = sum([a[7] for a in agentes])
    
    st.subheader(f"💵 Lucro Total: :green[${lucro_tropa:,.2f}]")

    tab_monitor, tab_historico = st.tabs(["🎯 Monitor do Grid", "📜 Histórico de Transações"])

    with tab_monitor:
        cols = st.columns(5)
        for i, ag in enumerate(agentes):
            id_ag, nome, end, priv, alvo, status, p_compra, l_acum, u_hash = ag
            
            # Lógica de Trade (Simulação de Hash Real)
            if btc <= alvo and status == "VIGILANCIA":
                new_h = f"0x{int(time.time())}BUY{id_ag}"
                db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultimo_hash=? WHERE id=?", (btc, new_h, id_ag))
                db.commit()
            elif status == "COMPRADO" and btc >= p_compra * (1 + (tp_pct/100)):
                lucro = btc - p_compra
                new_h = f"0x{int(time.time())}SELL{id_ag}"
                db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=?, ultimo_hash=? WHERE id=?", (l_acum + lucro, new_h, id_ag))
                db.commit()

            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{nome}**")
                    st.write(f"Lucro: ${l_acum:,.2f}")
                    if status == "COMPRADO": st.success("HOLDING")
                    else: st.info("VIGILANDO")

    with tab_historico:
        st.write("### 🔑 Hashes de Movimentação (Copie abaixo)")
        df_hist = pd.DataFrame(agentes, columns=['ID', 'Agente', 'Carteira', 'Privada', 'Alvo', 'Status', 'P.Compra', 'Lucro', 'Hash'])
        
        for _, row in df_hist[df_hist['Hash'] != ""].iterrows():
            col_a, col_b = st.columns([1, 4])
            col_a.write(f"**{row['Agente']}**")
            # O campo st.code já vem com botão de copiar automático do Streamlit
            col_b.code(row['Hash'], language="text")
            st.divider()

except sqlite3.OperationalError:
    st.error("⚠️ Banco de dados desalinhado. Clique em 'REINICIAR E CORRIGIR ESTRUTURA' no menu lateral.")

time.sleep(10)
st.rerun()