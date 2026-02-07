import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v12", layout="wide")

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.0")
    senha = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha == st.secrets.get("SECRET_KEY", "mestre2026"):
            st.session_state.logado = True
            st.rerun()
        else: st.error("Incorreta")
    st.stop()

# --- BANCO DE DADOS v6 (SUPORTE A 50 AGENTES) ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
db.commit()

# --- MOTOR DE PREÇO (MULTI-FONTE) ---
def pegar_preco():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()['price'])
    except:
        try: return float(requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDT").json()['result']['XBTUSDT']['c'][0])
        except: return None

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v12.0 | 50 SNIPERS")
btc = pegar_preco()

if btc:
    st.metric("BTC ATUAL", f"${btc:,.2f}")
    
    with st.sidebar:
        st.header("⚙️ COMANDO CENTRAL")
        pk_m = st.text_input("PK_01 (Saldo: 24 POL):", type="password")
        novo_topo = st.number_input("Novo Topo do Grid ($):", value=btc)
        
        if st.button("🚀 LANÇAR 50 SNIPERS (GRID DINÂMICO)"):
            db.execute("DELETE FROM agentes_v6")
            novos = []
            for i in range(50):
                acc = Account.create()
                alvo = novo_topo - (i * 150) # Distância de $150 entre os 50 agentes
                novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo, "VIGILANCIA", 0.0, "Iniciado"))
            db.executemany("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)", novos)
            db.commit()
            st.rerun()
            
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()

    # --- TABELA DE RELATÓRIO (ITEM 2) ---
    tab1, tab2 = st.tabs(["🎯 Monitor do Grid", "📊 Relatório de Operações"])
    
    with tab1:
        agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
        if agentes:
            cols = st.columns(5)
            for idx, ag in enumerate(agentes):
                with cols[idx % 5]:
                    with st.container(border=True):
                        st.write(f"**{ag[1]}**")
                        st.caption(f"Alvo: ${ag[4]:,.0f}")
                        if ag[5] == "COMPRADO": st.success(f"P: ${ag[6]:,.0f}")
                        else: st.info(ag[5])
        else: st.warning("Aguardando lançamento do batalhão de 50 agentes.")

    with tab2:
        st.subheader("Histórico em Tempo Real")
        if agentes:
            import pandas as pd
            df = pd.DataFrame(agentes, columns=['ID', 'Nome', 'Endereço', 'Privada', 'Alvo', 'Status', 'Preço Compra', 'Última Ação'])
            st.dataframe(df[['Nome', 'Status', 'Preço Compra', 'Última Ação']], use_container_width=True)

else:
    st.error("Reconectando à rede...")

time.sleep(30)
st.rerun()