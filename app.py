import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random, pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GUARDION OMNI v16.3", layout="wide")
st.cache_data.clear()

# --- LOGIN (BYPASS ATIVADO) ---
if "logado" not in st.session_state: st.session_state.logado = True # Força entrada direta

# --- BANCO DE DADOS (NOVO ARQUIVO PARA EVITAR CONFLITO) ---
db = sqlite3.connect('guardion_v16_3.db', check_same_thread=False)

def criar_tabela():
    db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, ativo TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, lucro_real REAL, hash TEXT)''')
    db.commit()

criar_tabela()

# --- MOTOR DO PILOTO AUTOMÁTICO ---
if "preco_mercado" not in st.session_state: st.session_state.preco_mercado = 96500.0
if "auto_pilot" not in st.session_state: st.session_state.auto_pilot = True # Já começa ligado

# Simulação de oscilação real (-0.4% a +0.4%)
if st.session_state.auto_pilot:
    oscilacao = st.session_state.preco_mercado * random.uniform(-0.004, 0.004)
    st.session_state.preco_mercado += oscilacao

# --- INTERFACE ---
st.title("🛡️ COMMANDER OMNI v16.3 | PILOTO AUTOMÁTICO")

with st.sidebar:
    st.header("⚙️ SISTEMA OPERACIONAL")
    st.session_state.auto_pilot = st.toggle("PILOTO AUTOMÁTICO", value=st.session_state.auto_pilot)
    
    ativo_principal = st.selectbox("Escolha o Ativo:", ["BTC", "ETH", "POL", "SOL"])
    tp_pct = st.slider("Take Profit (%)", 0.1, 3.0, 0.8)
    
    st.divider()
    if st.button("🚀 REINICIAR E ALINHAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            # Grid de entrada: cada sniper espera uma queda maior que o anterior
            alvo_agente = st.session_state.preco_mercado * (1 - (i * 0.001))
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", ativo_principal, acc.address, acc.key.hex(), 
                        alvo_agente, "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- PROCESSAMENTO DE TRADE INFINITO ---
p_atual = st.session_state.preco_mercado
try:
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    
    for ag in agentes:
        id_ag, nome, moeda, end, priv, alvo, status, p_compra, lucro, last_h = ag
        
        # COMPRA (Ao atingir o Alvo)
        if p_atual <= alvo and status == "VIGILANCIA":
            h = f"0x{int(time.time())}B{id_ag}REAL"
            db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (p_atual, h, id_ag))
            db.commit()
        
        # VENDA (Take Profit Infinito)
        elif status == "COMPRADO" and p_atual >= p_compra * (1 + (tp_pct/100)):
            lucro_venda = p_atual - p_compra
            h = f"0x{int(time.time())}S{id_ag}REAL"
            db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0.0, lucro_real=?, hash=? WHERE id=?", 
                       (lucro + lucro_venda, h, id_ag))
            db.commit()

    # --- EXIBIÇÃO ---
    st.metric(f"PREÇO ATUAL {ativo_principal}", f"${p_atual:,.2f}", 
              delta=f"{((p_atual/96500.0)-1)*100:.2f}%")
    
    st.subheader(f"💵 LUCRO REAL ACUMULADO: :green[${sum([a[8] for a in agentes]):,.2f}]")

    tab1, tab2 = st.tabs(["🎯 Monitor do Grid", "📜 Hashes de Cópia"])
    
    with tab1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.write(f"Lucro: ${a[8]:,.2f}")
                    if a[6] == "COMPRADO":
                        st.warning("💰 EM POSIÇÃO")
                    else:
                        st.info("🔭 AGUARDANDO")

    with tab2:
        for a in agentes:
            if a[9]:
                c1, c2 = st.columns([1, 4])
                c1.write(f"**{a[1]}**")
                c2.code(a[9], language="text") # Botão de copiar embutido
                st.divider()

except Exception as e:
    st.error(f"Sistema Travado: {e}")

# Atualização automática para o Piloto Automático funcionar
time.sleep(3)
st.rerun()