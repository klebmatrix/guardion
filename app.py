import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, secrets
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="GUARDION OMNI v10.3", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# --- TRATAMENTO DOS SECRETS (LIMPEZA DE CHAVE) ---
def carregar_pk():
    pk = st.secrets.get("PK_MESTRE")
    if pk:
        pk = pk.strip() # Remove espaços acidentais
        if not pk.startswith("0x") and len(pk) == 64:
            pk = "0x" + pk
        return pk
    return None

PK_MESTRE = carregar_pk()

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('guardion_data.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    stop_loss REAL, status TEXT, ultima_acao TEXT, data_criacao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- MOTOR DE LOGÍSTICA ---
def auto_abastecer(addr):
    if not PK_MESTRE: return
    try:
        acc_mestre = Account.from_key(PK_MESTRE)
        saldo_wei = w3.eth.get_balance(addr)
        if saldo_wei < w3.to_wei(0.1, 'ether'):
            tx = {
                'nonce': w3.eth.get_transaction_count(acc_mestre.address),
                'to': addr, 'value': w3.to_wei(0.5, 'ether'),
                'gas': 21000, 'gasPrice': w3.eth.gas_price, 'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            st.toast(f"⛽ Gas enviado para {addr[:6]}", icon="🚀")
    except Exception as e:
        st.error(f"Erro no envio de gas: {e}")

def get_price(coin):
    try:
        ids = {"WBTC": "bitcoin", "ETH": "ethereum"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        res = requests.get(url, timeout=5).json()
        return res[ids[coin]]['usd']
    except: return None

# --- INTERFACE DE COMANDO ---
st.title("🛡️ COMMANDER OMNI | SENTINEL v10.3")

# --- 1. STATUS DA CONEXÃO MESTRE (DIAGNÓSTICO) ---
with st.expander("🔐 Status da Chave Mestre", expanded=True):
    if not PK_MESTRE:
        st.error("❌ Variável 'PK_MESTRE' não encontrada nos Secrets do Streamlit.")
        st.info("Dica: No Streamlit Cloud, vá em Settings > Secrets e adicione: PK_MESTRE = 'sua_chave'")
    else:
        try:
            acc_mestre = Account.from_key(PK_MESTRE)
            s_mestre_pol = round(w3.from_wei(w3.eth.get_balance(acc_mestre.address), 'ether'), 2)
            st.success(f"✅ Wallet Mestre Conectada: {acc_mestre.address}")
            
            # Alerta de Saldo (Seus 24 POL)
            c1, c2 = st.columns(2)
            c1.metric("Saldo Tesouraria", f"{s_mestre_pol} POL")
            if s_mestre_pol < 2.0:
                st.error("🚨 SALDO CRÍTICO NA MESTRE!")
            elif s_mestre_pol < 12.5:
                st.warning("⚠️ Saldo insuficiente para abastecer 25 agentes (precisa de 12.5 POL).")
        except Exception as e:
            st.error(f"❌ Chave Inválida: O formato da PK_MESTRE nos Secrets está incorreto.")
            st.code(f"Erro técnico: {e}")

st.divider()

# --- RESTANTE DO APP (FÁBRICA E MONITORES) ---
agentes = db.execute("SELECT * FROM modulos").fetchall()

with st.sidebar:
    st.header("🏭 Fábrica de Grid")
    qtd = st.select_slider("Soldados:", options=[1, 5, 10, 25, 50], value=25)
    ativo = st.selectbox("Ativo", ["WBTC", "ETH"])
    p_topo = st.number_input("Preço Inicial:", value=102500.0)
    dist = st.number_input("Distância ($):", value=200.0)
    
    if st.button(f"🚀 LANÇAR {qtd} AGENTES"):
        if not PK_MESTRE:
            st.error("Impossível lançar sem PK_MESTRE.")
        else:
            novos = []
            for i in range(qtd):
                acc = Account.create()
                p_alvo = p_topo - (i * dist)
                novos.append((f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), ativo, p_alvo, 
                              0.0, 10.0, 5.0, "VIGILANCIA", f"Alvo: ${p_alvo}", 
                              datetime.now().strftime("%H:%M")))
            db.executemany("INSERT INTO modulos (nome, endereco, privada, alvo, preco_gatilho, preco_compra, lucro_esperado, stop_loss, status, ultima_acao, data_criacao) VALUES (?,?,?,?,?,?,?,?,?,?,?)", novos)
            db.commit()
            st.rerun()

    if st.button("🧹 RESET TOTAL"):
        db.execute("DELETE FROM modulos")
        db.commit()
        st.rerun()

if agentes:
    st.subheader("⛽ Tanques do Batalhão")
    cols = st.columns(4)
    for idx, ag in enumerate(agentes):
        with cols[idx % 4]:
            with st.container(border=True):
                try:
                    s_pol = round(w3.from_wei(w3.eth.get_balance(ag[2]), 'ether'), 3)
                except: s_pol = 0.0
                st.write(f"**{ag[1]}**")
                st.progress(min(s_pol / 0.5, 1.0))
                st.caption(f"{s_pol} POL | ${ag[5]}")
                if ag[9] == "VIGILANCIA": auto_abastecer(ag[2])

    st.divider()
    preco_v = get_price(agentes[0][4])
    st.metric(f"Preço Atual {agentes[0][4]}", f"${preco_v}")
    
    for ag in agentes:
        if ag[9] == "VIGILANCIA" and preco_v and preco_v <= ag[5]:
            db.execute("UPDATE modulos SET status='POSICIONADO', preco_compra=?, ultima_acao='COMPRADO' WHERE id=?", (preco_v, ag[0]))
            db.commit()
            st.rerun()
else:
    st.info("Aguardando ordem de lançamento.")

time.sleep(60)
st.rerun()