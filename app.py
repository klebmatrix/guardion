import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, pandas as pd

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="GUARDION OMNI v12.1", layout="wide", initial_sidebar_state="collapsed")

# --- LOGIN (SECRETS) ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("🔐 QG GUARDION v12.1")
    senha = st.text_input("Chave do QG:", type="password")
    if st.button("ENTRAR"):
        if senha == st.secrets.get("SECRET_KEY", "mestre2026"):
            st.session_state.logado = True
            st.rerun()
        else: st.error("Incorreta")
    st.stop()

# --- CONEXÃO BANCO DE DADOS ---
db = sqlite3.connect('guardion_v6.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS agentes_v6 
                (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                alvo REAL, status TEXT, preco_compra REAL, ultima_acao TEXT)''')
db.commit()

# --- MOTOR DE PREÇO ---
def pegar_preco():
    try: return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()['price'])
    except: return None

# --- MOTOR DE EXECUÇÃO ATIVA (TAKE PROFIT INFINITO) ---
def processar_operacoes(btc_atual, porcentagem_tp):
    agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
    for ag in agentes:
        id_ag, nome, _, _, alvo, status, preco_compra, _ = ag
        
        # 🟢 GATILHO DE COMPRA (Preço caiu abaixo do Alvo do Grid)
        if btc_atual <= alvo and status == "VIGILANCIA":
            nova_acao = f"✅ Comprado a ${btc_atual:,.2f}"
            db.execute("UPDATE agentes_v6 SET status='COMPRADO', preco_compra=?, ultima_acao=? WHERE id=?", 
                       (btc_atual, nova_acao, id_ag))
            db.commit()
            st.toast(f"🎯 {nome}: COMPRADO!")

        # 🔴 GATILHO DE VENDA (TAKE PROFIT ATIVO INFINITO)
        elif status == "COMPRADO":
            alvo_venda = preco_compra * (1 + (porcentagem_tp / 100))
            if btc_atual >= alvo_venda:
                lucro = btc_atual - preco_compra
                nova_acao = f"💰 Lucro: ${lucro:,.2f} | Resetando..."
                # Volta para VIGILANCIA para reentrada infinita
                db.execute("UPDATE agentes_v6 SET status='VIGILANCIA', preco_compra=0.0, ultima_acao=? WHERE id=?", 
                           (nova_acao, id_ag))
                db.commit()
                st.toast(f"💸 {nome}: TAKE PROFIT BATIDO!")

# --- UI PRINCIPAL ---
st.title("🛡️ COMMANDER OMNI v12.1 | 50 SNIPERS")
btc = pegar_preco()

if btc:
    # Telemetria Superior
    c1, c2, c3 = st.columns(3)
    c1.metric("BTC ATUAL", f"${btc:,.2f}")
    
    with st.sidebar:
        st.header("⚙️ COMANDO CENTRAL")
        tp_input = st.slider("Take Profit (%)", 0.5, 10.0, 2.0)
        distancia = st.number_input("Distância Grid ($)", value=150)
        
        if st.button("🚀 REINICIALIZAR 50 SNIPERS"):
            db.execute("DELETE FROM agentes_v6")
            novos = [(f"SNPR-{i+1:02d}", Account.create().address, Account.create().key.hex(), btc - (i * distancia), "VIGILANCIA", 0.0, "Pronto") for i in range(50)]
            db.executemany("INSERT INTO agentes_v6 (nome, endereco, privada, alvo, status, preco_compra, ultima_acao) VALUES (?,?,?,?,?,?,?)", novos)
            db.commit()
            st.rerun()

    # Processamento em tempo real
    processar_operacoes(btc, tp_input)

    # Painel de Monitoramento
    tab1, tab2 = st.tabs(["🎯 Monitor do Grid", "📊 Relatório de Operações"])
    
    with tab1:
        agentes = db.execute("SELECT * FROM agentes_v6").fetchall()
        if agentes:
            cols = st.columns(5)
            for idx, ag in enumerate(agentes):
                with cols[idx % 5]:
                    cor = "green" if ag[5] == "COMPRADO" else "normal"
                    with st.container(border=True):
                        st.markdown(f"### {ag[1]}")
                        st.caption(f"🎯 Alvo Compra: ${ag[4]:,.0f}")
                        if ag[5] == "COMPRADO":
                            st.write(f"📈 P. Compra: **${ag[6]:,.0f}**")
                            st.write(f"🚀 Alvo TP: **${ag[6]*(1+(tp_input/100)):,.0f}**")
                        else:
                            st.info("Aguardando Preço...")
        else: st.warning("Exército desativado. Use o menu lateral.")

    with tab2:
        if agentes:
            df = pd.DataFrame(agentes, columns=['ID', 'Nome', 'Endereço', 'Privada', 'Alvo', 'Status', 'Preço Compra', 'Última Ação'])
            st.dataframe(df[['Nome', 'Status', 'Preço Compra', 'Última Ação']], use_container_width=True)

else:
    st.error("Falha na conexão com a rede Binance/Kraken.")

# Refresh Automático para o Loop Infinito
time.sleep(30)
st.rerun()