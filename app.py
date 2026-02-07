import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v14.7", layout="wide")

# --- LOGIN ---
SENHA_MESTRA = st.secrets.get("SECRET_KEY", "mestre2026")
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 QG GUARDION - COMANDO SIN")
    if st.text_input("Chave:", type="password") == SENHA_MESTRA:
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- DB: ALINHAMENTO DE TODAS AS COLUNAS ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)

def reset_sistema_sin():
    db.execute("DROP TABLE IF EXISTS agentes_v6")
    db.execute('''CREATE TABLE agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, ativo TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_acumulado REAL, ultimo_hash TEXT)''')
    db.commit()

# --- UI COMANDO ---
st.title("🛡️ COMMANDER OMNI | SINAL ATIVO (SIN)")

with st.sidebar:
    st.header("🎮 CONTROLE DE ATIVOS")
    
    # Seletor de Ativo e Movimentação
    moeda = st.selectbox("Escolha o Ativo:", ["POL", "BTC", "ETH", "SOL", "LINK"])
    p_atual = st.number_input(f"Preço SIN {moeda} ($):", value=1.0, step=0.01, format="%.4f")
    
    tp_pct = st.slider("Take Profit (%)", 0.1, 5.0, 1.2)
    
    st.divider()
    if st.button("🚀 REINICIAR GRID (FIX SIN ERROR)"):
        reset_sistema_sin()
        ativos = ["POL", "BTC", "ETH", "SOL", "LINK"]
        idx = 0
        for a in ativos:
            for i in range(10): # 10 Snipers por moeda
                acc = Account.create()
                db.execute("INSERT INTO agentes_v6 VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (idx, f"SNPR-{idx+1:02d}", a, acc.address, acc.key.hex(), p_atual * (1 - (i*0.01)), "VIGILANCIA", 0.0, 0.0, ""))
                idx += 1
        db.commit()
        st.rerun()

# --- MOTOR DE EXECUÇÃO INFINITA ---
try:
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    
    for ag in agentes:
        id_ag, nome, ativo_ag, end, priv, alvo, status, p_compra, l_acum, u_hash = ag
        
        if ativo_ag == moeda:
            # COMPRA (SIN BAIXO)
            if p_atual <= alvo and status == "VIGILANCIA":
                h = f"0x{int(time.time())}SIN_B_{id_ag}"
                db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultimo_hash=? WHERE id=?", (p_atual, h, id_ag))
            
            # VENDA (SIN ALTO - INFINITO)
            elif status == "COMPRADO" and p_atual >= p_compra * (1 + (tp_pct/100)):
                lucro = p_atual - p_compra
                h = f"0x{int(time.time())}SIN_S_{id_ag}"
                db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, lucro_acumulado=?, ultimo_hash=? WHERE id=?", 
                           (l_acum + lucro, h, id_ag))
    db.commit()

    # --- EXIBIÇÃO ---
    lucro_total = sum([a[8] for a in agentes])
    st.success(f"### 💵 LUCRO TOTAL SIN: ${lucro_total:,.2f}")

    t1, t2 = st.tabs(["🎯 Monitor SIN", "📜 Hashes de Cópia"])
    
    with t1:
        ag_ativos = [a for a in agentes if a[2] == moeda]
        cols = st.columns(5)
        for i, a in enumerate(ag_ativos):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}** ({a[2]})")
                    st.write(f"Lucro: :green[${a[8]:,.2f}]")
                    if a[6] == "COMPRADO": st.warning("HOLDING")
                    else: st.info("VIGILANDO")

    with t2:
        st.write("### 🔑 IDs de Transação")
        df_h = pd.DataFrame(agentes, columns=['ID','Nome','Ativo','End','Key','Alvo','Status','P.Compra','Lucro','Hash'])
        for _, row in df_h[df_h['Hash'] != ""].iterrows():
            c1, c2 = st.columns([1, 4])
            c1.write(f"**{row['Nome']}**")
            c2.code(row['Hash'], language="text") # Botão de copiar nativo
            st.divider()

except Exception as e:
    st.error("ERRO DE SINAL (SIN). Clique em REINICIAR GRID no menu lateral.")

time.sleep(10)
st.rerun()