import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v14.1", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"

# --- LOGIN ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY")
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 ACESSO AO QG")
    senha = st.text_input("Chave:", type="password")
    if st.button("ENTRAR"):
        if senha == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- DB COM ESTRUTURA BLINDADA ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

# Função para garantir que a tabela tenha as 8 colunas exatas
def preparar_db():
    db.execute("DROP TABLE IF EXISTS agentes_v6") # Reset para alinhar as colunas
    db.execute('''CREATE TABLE agentes_v6 
                (id INTEGER PRIMARY KEY, 
                 nome TEXT, 
                 endereco TEXT, 
                 privada TEXT, 
                 alvo REAL, 
                 status TEXT, 
                 preco_compra REAL, 
                 lucro_acumulado REAL)''')
    db.commit()

# --- INTERFACE E CONTROLE INTERNO ---
st.title("🛡️ COMMANDER OMNI v14.1 | LUCRO EXPLÍCITO")

if "btc_interno" not in st.session_state:
    st.session_state.btc_interno = 96000.0

with st.sidebar:
    st.header("🎮 CONTROLE DO AGENTE")
    st.session_state.btc_interno = st.number_input("Preço Interno BTC ($):", value=st.session_state.btc_interno, step=50.0)
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.5)
    
    st.divider()
    if st.button("🚀 REINICIAR E ALINHAR 50 SNIPERS"):
        preparar_db()
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes_v6 VALUES (?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), st.session_state.btc_interno - (i*100), "VIGILANCIA", 0.0, 0.0))
        db.commit()
        st.rerun()

# --- PROCESSAMENTO ---
btc = st.session_state.btc_interno
# Busca todos os dados da tabela
agentes = db.execute("SELECT id, nome, endereco, privada, alvo, status, preco_compra, lucro_acumulado FROM agentes_v6").fetchall()

lucro_total_geral = 0
if agentes:
    cols = st.columns(5)
    for i, ag in enumerate(agentes):
        # Desempacotamento seguro das 8 colunas
        id_ag, nome, end, priv, alvo, status, p_compra, l_acum = ag
        lucro_total_geral += l_acum
        
        # Logica de Compra
        if btc <= alvo and status == "VIGILANCIA":
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=? WHERE id=?", (btc, id_ag))
            db.commit()
            
        # Logica de Take Profit (Reset Ativo Infinito)
        elif status == "COMPRADO":
            if btc >= p_compra * (1 + (tp_pct/100)):
                lucro_da_venda = btc - p_compra
                novo_lucro_total = l_acum + lucro_da_venda
                db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=? WHERE id=?", (novo_lucro_total, id_ag))
                db.commit()

        # Exibição nos Cards
        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"**{nome}**")
                if status == "COMPRADO":
                    st.success(f"HOLDING")
                    st.caption(f"C: ${p_compra:,.0f}")
                else:
                    st.info(f"VIGILANDO")
                    st.caption(f"Alvo: ${alvo:,.0f}")
                st.write(f"💰 Lucro: **${l_acum:,.2f}**")

    st.divider()
    st.markdown(f"## 💵 LUCRO TOTAL ACUMULADO: :green[${lucro_total_geral:,.2f}]")
else:
    st.warning("Clique em 'REINICIAR E ALINHAR' para criar as carteiras e começar.")

# Auto-refresh para manter o sistema vivo
time.sleep(10)
st.rerun()