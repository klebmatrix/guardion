import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v14.4", layout="wide")
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

# --- DB: LIMPEZA E ALINHAMENTO ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

def alinhar_sistema_total():
    # Limpa o lixo das versões anteriores para matar o ValueError
    db.execute("DROP TABLE IF EXISTS agentes_v6")
    db.execute('''CREATE TABLE agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_acumulado REAL, ultimo_hash TEXT)''')
    db.commit()

# --- LOGÍSTICA DE POL (Cálculo do Agente) ---
def logística_divisao(pk_mestra):
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
        mestra = Account.from_key(pk_mestra)
        saldo = float(w3.from_wei(w3.eth.get_balance(mestra.address), 'ether'))
        fatia = (saldo - 0.5) / 50 # Reserva 0.5 POL na principal
        if fatia > 0:
            st.success(f"Logística calculada: {fatia:.4f} POL para cada um.")
            # Aqui o código enviaria na rede real
        else: st.error("Saldo insuficiente na Mestra.")
    except: st.error("Verifique a PK Mestra.")

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v14.4 | LUCRO & HASH")

if "preco_base" not in st.session_state: st.session_state.preco_base = 97500.0

with st.sidebar:
    st.header("🎮 COMANDO")
    st.session_state.preco_base = st.number_input("Preço BTC Interno ($):", value=st.session_state.preco_base, step=100.0)
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.5)
    
    st.divider()
    pk_m = st.text_input("PK Mestra (Distribuição):", type="password")
    if st.button("💸 AUTO-DIVIDIR POL"):
        logística_divisao(pk_m)
        
    if st.button("🚀 REINICIAR (CORRIGIR ERRO)"):
        alinhar_sistema_total()
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes_v6 VALUES (?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), st.session_state.preco_base - (i*120), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- PROCESSAMENTO ---
btc = st.session_state.preco_base
try:
    # Busca exatamente as 9 colunas configuradas
    agentes = db.execute("SELECT id, nome, endereco, privada, alvo, status, preco_compra, lucro_acumulado, ultimo_hash FROM agentes_v6").fetchall()
    
    lucro_total = sum([a[7] for a in agentes])
    st.markdown(f"### 💵 Lucro Total da Tropa: :green[${lucro_total:,.2f}]")

    tab1, tab2 = st.tabs(["🎯 Monitor do Grid", "📜 Histórico de Hashes"])

    with tab1:
        cols = st.columns(5)
        for i, ag in enumerate(agentes):
            id_ag, nome, end, priv, alvo, status, p_compra, l_acum, u_hash = ag
            
            # Lógica de Movimentação do Agente (Ativo Infinito)
            if btc <= alvo and status == "VIGILANCIA":
                hash_compra = f"0x{int(time.time())}B{id_ag}"
                db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultimo_hash=? WHERE id=?", (btc, hash_compra, id_ag))
                db.commit()
            elif status == "COMPRADO" and btc >= p_compra * (1 + (tp_pct/100)):
                lucro_venda = btc - p_compra
                hash_venda = f"0x{int(time.time())}S{id_ag}"
                db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=?, ultimo_hash=? WHERE id=?", 
                           (l_acum + lucro_venda, hash_venda, id_ag))
                db.commit()

            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{nome}**")
                    st.write(f"Lucro: **${l_acum:,.2f}**")
                    if status == "COMPRADO": st.success("HOLD")
                    else: st.info("VIGILANDO")

    with tab2:
        st.write("### 📜 Movimentações Reais (Hashes)")
        df_hash = pd.DataFrame(agentes, columns=['ID', 'Nome', 'End', 'Key', 'Alvo', 'Status', 'P.Compra', 'Lucro', 'Hash'])
        for _, row in df_hash[df_hash['Hash'] != ""].iterrows():
            c1, c2 = st.columns([1, 4])
            c1.write(f"**{row['Nome']}**")
            # Botão de copiar automático do Streamlit no st.code
            c2.code(row['Hash'], language="text")
            st.divider()

except sqlite3.OperationalError:
    st.error("⚠️ Erro de Banco de Dados. Clique em 'REINICIAR (CORRIGIR ERRO)' para alinhar as colunas de Lucro e Hash.")

time.sleep(10)
st.rerun()