import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v14.5", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"

# --- LOGIN ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 QG GUARDION - MODO PERPÉTUO")
    if st.text_input("Chave do QG:", type="password") == SENHA_MESTRA:
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- DB: ESTRUTURA PARA OPERAÇÃO INFINITA ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

def reset_db_infinito():
    db.execute("DROP TABLE IF EXISTS agentes_v6")
    db.execute('''CREATE TABLE agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_acumulado REAL, ultimo_hash TEXT)''')
    db.commit()

# --- UI E CONTROLE DO AGENTE ---
st.title("🛡️ COMMANDER OMNI | OPERAÇÃO INFINITA ATIVA")

if "preco_base" not in st.session_state: st.session_state.preco_base = 98000.0

with st.sidebar:
    st.header("⚙️ MOTOR DE MERCADO")
    # Você move o preço e o robô executa o ciclo infinito
    st.session_state.preco_base = st.number_input("Mover Preço BTC ($):", value=st.session_state.preco_base, step=50.0)
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.0)
    
    st.divider()
    if st.button("🚀 REINICIAR GRID (CORRIGIR ERROS)"):
        reset_db_infinito()
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes_v6 VALUES (?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), st.session_state.preco_base - (i*100), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- PROCESSAMENTO INFINITO (VENDA E COMPRA) ---
btc = st.session_state.preco_base
try:
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    lucro_total = sum([a[7] for a in agentes])
    
    st.markdown(f"## 💵 LUCRO TOTAL DA TROPA: :green[${lucro_total:,.2f}]")

    tab1, tab2 = st.tabs(["🎯 Monitor do Grid", "📜 Histórico de Transações (Copiar Hash)"])

    with tab1:
        cols = st.columns(5)
        for i, ag in enumerate(agentes):
            id_ag, nome, end, priv, alvo, status, p_compra, l_acum, u_hash = ag
            
            # 1. CICLO DE COMPRA (ENTRADA)
            if btc <= alvo and status == "VIGILANCIA":
                hash_id = f"0x{int(time.time())}B{id_ag}"
                db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultimo_hash=? WHERE id=?", (btc, hash_id, id_ag))
                db.commit()
            
            # 2. CICLO DE VENDA (TAKE PROFIT INFINITO)
            elif status == "COMPRADO" and btc >= p_compra * (1 + (tp_pct/100)):
                lucro_da_vez = btc - p_compra
                hash_id = f"0x{int(time.time())}S{id_ag}"
                # IMPORTANTE: Reseta para VIGILANCIA para operar infinitamente
                db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=?, ultimo_hash=? WHERE id=?", 
                           (l_acum + lucro_da_vez, hash_id, id_ag))
                db.commit()

            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{nome}**")
                    if status == "COMPRADO":
                        st.success("💰 COMPRADO")
                        st.caption(f"Em: ${p_compra:,.0f}")
                    else:
                        st.info("🔭 VIGILANDO")
                        st.caption(f"Alvo: ${alvo:,.0f}")
                    st.markdown(f"**LUCRO: ${l_acum:,.2f}**")

    with tab2:
        st.subheader("📜 Rastro das Operações (Clique para Copiar)")
        df = pd.DataFrame(agentes, columns=['ID', 'Agente', 'Carteira', 'Key', 'Alvo', 'Status', 'P.Compra', 'Lucro', 'Hash'])
        for _, row in df[df['Hash'] != ""].iterrows():
            c1, c2 = st.columns([1, 4])
            c1.write(f"**{row['Agente']}**")
            c2.code(row['Hash'], language="text") # Botão de copiar embutido
            st.divider()

except Exception:
    st.error("⚠️ Banco de dados em conflito. Use o botão REINICIAR GRID no menu lateral.")

# Refresh constante para operação em tempo real
time.sleep(5)
st.rerun()