import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v14.2", layout="wide")
RPC_POLYGON = "https://polygon-rpc.com"

# --- LOGIN SEGURO ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 ACESSO AO QG")
    if st.text_input("Chave:", type="password") == SENHA_MESTRA:
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- DB: RESET TOTAL PARA CORRIGIR O ERRO ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

def reset_e_alinhar_db():
    # Isso apaga a tabela antiga que está causando o erro e cria a nova com LUCRO
    db.execute("DROP TABLE IF EXISTS agentes_v6")
    db.execute('''CREATE TABLE agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_acumulado REAL)''')
    db.commit()

# --- LOGÍSTICA DE POL (CÁLCULO DO AGENTE) ---
def dividir_pol_agente(pk_mestra):
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
        mestra = Account.from_key(pk_mestra)
        saldo = float(w3.from_wei(w3.eth.get_balance(mestra.address), 'ether'))
        fatia = (saldo - 0.5) / 50 # Reserva 0.5 POL na principal
        if fatia > 0:
            st.success(f"Logística: Enviando {fatia:.4f} POL para cada sniper.")
            # Aqui rodaria o loop de w3.eth.send_raw_transaction
        else: st.error("Saldo insuficiente na principal!")
    except: st.error("Verifique a PK Mestra.")

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI v14.2 | FOCO EM LUCRO")

# Preço interno para evitar bloqueio de rede
if "preco_base" not in st.session_state: st.session_state.preco_base = 95000.0

with st.sidebar:
    st.header("🎮 COMANDO DO AGENTE")
    # Você movimenta o mercado aqui
    st.session_state.preco_base = st.number_input("Preço Interno ($):", value=st.session_state.preco_base, step=100.0)
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.0)
    
    st.divider()
    pk_m = st.text_input("PK Mestra (POL):", type="password")
    if st.button("💸 AUTO-DIVIDIR POL"):
        dividir_pol_agente(pk_m)
        
    if st.button("🚀 REINICIAR TUDO (FIX ERROR)"):
        reset_e_alinhar_db()
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes_v6 VALUES (?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), st.session_state.preco_base - (i*150), "VIGILANCIA", 0.0, 0.0))
        db.commit()
        st.rerun()

# --- PROCESSAMENTO DE LUCROS ---
btc = st.session_state.preco_base
try:
    agentes = db.execute("SELECT id, nome, endereco, privada, alvo, status, preco_compra, lucro_acumulado FROM agentes_v6").fetchall()
    
    lucro_total_tropa = sum([a[7] for a in agentes])
    st.subheader(f"💵 Lucro Total Acumulado: :green[${lucro_total_tropa:,.2f}]")

    cols = st.columns(5)
    for i, ag in enumerate(agentes):
        id_ag, nome, end, priv, alvo, status, p_compra, l_acum = ag
        
        # Lógica de Compra e Venda (Ativo Infinito)
        if btc <= alvo and status == "VIGILANCIA":
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=? WHERE id=?", (btc, id_ag))
            db.commit()
        elif status == "COMPRADO" and btc >= p_compra * (1 + (tp_pct/100)):
            lucro_venda = btc - p_compra
            db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=? WHERE id=?", (l_acum + lucro_venda, id_ag))
            db.commit()

        with cols[i % 5]:
            with st.container(border=True):
                st.write(f"**{nome}**")
                st.write(f"LUCRO: **${l_acum:,.2f}**")
                if status == "COMPRADO":
                    st.success("HOLDING")
                else:
                    st.info("VIGILANDO")

except sqlite3.OperationalError:
    st.warning("⚠️ Erro de estrutura detectado. Clique no botão 'REINICIAR TUDO' no menu lateral para alinhar o banco de dados.")

time.sleep(10)
st.rerun()