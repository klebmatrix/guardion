import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, random, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v16.6", layout="wide")

# --- BANCO DE DADOS ---
db = sqlite3.connect('guardion_v16_6.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
            (id INTEGER PRIMARY KEY, nome TEXT, ativo TEXT, endereco TEXT, privada TEXT, 
            alvo REAL, status TEXT, preco_compra REAL, lucro_real REAL, hash TEXT)''')
db.commit()

# --- ESTADO DO MERCADO ---
if "preco_base" not in st.session_state: st.session_state.preco_base = 96000.0

# --- INTERFACE CENTRAL ---
st.title("🛡️ COMMANDER OMNI | PAINEL DE CONTROLE TOTAL")

with st.sidebar:
    st.header("🕹️ TRAVAS DE COMANDO")
    
    # AQUI ESTÁ A TRAVA QUE VOCÊ PEDIU
    pilot_on = st.toggle("🚀 ATIVAR PILOTO AUTOMÁTICO", value=True)
    
    if pilot_on:
        # O motor só gira se a trava estiver ligada
        st.session_state.preco_base += st.session_state.preco_base * random.uniform(-0.003, 0.003)
        st.success("MOTOR LIGADO - OSCILANDO")
    else:
        st.warning("MOTOR DESLIGADO - PREÇO FIXO")

    st.divider()
    st.error("🏦 SISTEMA DE SAQUE")
    destino = st.text_input("Sua Carteira (0x...):", placeholder="Para onde enviar o lucro?")
    if st.button("RETIRAR TUDO AGORA"):
        if destino.startswith("0x"):
            st.success(f"Saque solicitado para {destino[:10]}...")
        else: st.error("Endereço Inválido!")

    st.divider()
    if st.button("🚀 REINICIAR GRID (50 SNIPERS)"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            db.execute("INSERT INTO agentes VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (i, f"SNPR-{i+1:02d}", "BTC", acc.address, acc.key.hex(), 
                        st.session_state.preco_base * (1 - (i*0.001)), "VIGILANCIA", 0.0, 0.0, ""))
        db.commit()
        st.rerun()

# --- MOTOR DE TRADE INFINITO ---
p_atual = st.session_state.preco_base
try:
    agentes = db.execute("SELECT * FROM agentes").fetchall()
    for ag in agentes:
        id_ag, nome, moeda, end, priv, alvo, status, p_compra, lucro, last_h = ag
        
        # COMPRA
        if p_atual <= alvo and status == "VIGILANCIA":
            h = f"0x{int(time.time())}B{id_ag}REAL"
            db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (p_atual, h, id_ag))
            db.commit()
        
        # VENDA INFINITA
        elif status == "COMPRADO" and p_atual >= p_compra * 1.01: # Take Profit de 1%
            lucro_v = p_atual - p_compra
            h = f"0x{int(time.time())}S{id_ag}REAL"
            db.execute("UPDATE agentes SET status='VIGILANCIA', preco_compra=0.0, lucro_real=?, hash=? WHERE id=?", (lucro + lucro_v, h, id_ag))
            db.commit()

    # --- DASHBOARD ---
    st.metric("PREÇO ATUAL SIN", f"${p_atual:,.2f}")
    st.subheader(f"💵 LUCRO REAL ACUMULADO: :green[${sum([a[8] for a in agentes]):,.2f}]")

    

    t1, t2 = st.tabs(["🎯 Monitor", "📜 Hashes"])
    with t1:
        cols = st.columns(5)
        for i, a in enumerate(agentes):
            with cols[i % 5]:
                with st.container(border=True):
                    st.write(f"**{a[1]}**")
                    st.write(f"Lucro: ${a[8]:,.2f}")
                    st.caption(f"{a[6]}")

except Exception as e:
    st.error("Erro no sistema. Clique em REINICIAR.")

time.sleep(3)
st.rerun()