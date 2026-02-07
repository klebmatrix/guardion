import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, datetime

# --- 1. CONFIGURAÇÃO E BANCO ---
st.set_page_config(page_title="GUARDION OMNI v15.4 REAL", layout="wide")

db = sqlite3.connect('guardion_real_v15.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, hash TEXT)''')
db.commit()

# Carregamento seguro da lista de agentes
agentes_raw = db.execute("SELECT * FROM agentes").fetchall()

# --- 2. SISTEMA DE ACESSO ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🛡️ QG GUARDION REAL")
    senha = st.text_input("Chave Mestre:", type="password")
    if st.button("DESBLOQUEAR"):
        if senha == st.secrets.get("SECRET_KEY", "mestre2026"):
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 3. CONEXÃO BLOCKCHAIN ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

def pegar_preco_btc():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price'])
    except: return None

# ABASTECIMENTO COM PROTEÇÃO DE NONCE (22 POL)
def abastecer_agentes(pk_mestre):
    try:
        mestre_acc = Account.from_key(pk_mestre)
        # Seleciona os primeiros 10 snipers
        alvo_agentes = db.execute("SELECT endereco FROM agentes LIMIT 10").fetchall()
        
        # Pega o nonce 'pending' para evitar atropelos na rede
        nonce = w3.eth.get_transaction_count(mestre_acc.address, 'pending')
        
        for ag in alvo_agentes:
            tx = {
                'nonce': nonce,
                'to': ag[0],
                'value': w3.to_wei(0.5, 'ether'), # Envia 0.5 POL
                'gas': 21000,
                'gasPrice': int(w3.eth.gas_price * 1.5), # Gás prioritário
                'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, pk_mestre)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            nonce += 1 # Incremento manual seguro
            time.sleep(1) # Delay técnico
        return True
    except Exception as e:
        st.sidebar.error(f"Erro de Rede: {str(e)}")
        return False

# --- 4. LÓGICA DE OPERAÇÃO ---
st.title("🛡️ COMMANDER OMNI v15.4")
btc = pegar_preco_btc()

if btc:
    st.metric("BTC/USDT ATUAL", f"${btc:,.2f}")
    for ag in agentes_raw:
        id_b, nome, addr, priv, alvo, status, p_compra, tx_h = ag
        # Verifica se o preço bateu no alvo e se o sniper está em vigília
        if status == "VIGILANCIA" and btc <= alvo:
            try:
                # Verifica saldo real antes de tentar disparar
                saldo_atual = w3.eth.get_balance(addr)
                if saldo_atual > 0:
                    tx = {
                        'nonce': w3.eth.get_transaction_count(addr),
                        'to': addr,
                        'value': 0,
                        'gas': 21000,
                        'gasPrice': w3.eth.gas_price,
                        'chainId': 137
                    }
                    signed = w3.eth.account.sign_transaction(tx, priv)
                    shs = w3.to_hex(w3.eth.send_raw_transaction(signed.raw_transaction))
                    db.execute("UPDATE agentes SET status='COMPRADO', preco_compra=?, hash=? WHERE id=?", (btc, shs, id_b))
                    db.commit()
            except:
                continue

# --- 5. PAINEL LATERAL (COMANDOS) ---
with st.sidebar:
    st.header("⚙️ COMANDO CENTRAL")
    pk_m = st.text_input("PK Carteira Mestre (22 POL):", type="password")
    
    if st.button("🚀 GERAR 50 SNIPERS"):
        db.execute("DELETE FROM agentes")
        for i in range(50):
            acc = Account.create()
            alvo_calc = btc - (i * 100) if btc else 100000 - (i * 100)
            db.execute("INSERT INTO agentes (nome, endereco, privada, alvo, status, hash) VALUES (?,?,?,?,?,?)",
                       (f"SNPR-{i+1:02d}", acc.address, acc.key.hex(), alvo_calc, "VIGILANCIA", "---"))
        db.commit()
        st.rerun()

    if st.button("⛽ ABASTECER AGENTES"):
        if pk_m:
            if abastecer_agentes(pk_m): st.success("Transações de POL enviadas!")
            else: st.error("Falha no abastecimento.")

# --- 6. VISUALIZAÇÃO ---
t1, t2 = st.tabs(["🎯 GRID DE VIGILÂNCIA", "📄 RELATÓRIO DE HASH (SHS)"])

with t1:
    if agentes_raw:
        cols = st.columns(5)
        for idx, ag in enumerate(agentes_raw):
            with cols[idx % 5]:
                with st.container(border=True):
                    st.write(f"**{ag[1]}**")
                    if "0x" in str(ag[7]):
                        st.success("EXECUTADO ✅")
                    else:
                        st.info(f"🎯 ${ag[4]:,.0f}")
                        # Verifica saldo para exibir no card
                        try:
                            s = w3.eth.get_balance(ag[2])
                            if s > 0: st.caption(f"💰 {w3.from_wei(s, 'ether'):.2f} POL")
                        except: pass

with t2:
    if agentes_raw:
        import pandas as pd
        df = pd.DataFrame(agentes_raw, columns=['ID','Nome','Endereço','Privada','Alvo','Status','Preço','Hash'])
        df['PolygonScan'] = df['Hash'].apply(lambda x: f"https://polygonscan.com/tx/{x}" if x.startswith('0x') else x)
        st.dataframe(df[['Nome', 'Status', 'Alvo', 'PolygonScan', 'Endereço']], width='stretch')

time.sleep(20)
st.rerun()