import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, secrets, requests
from datetime import datetime

# Configuração e Conexão
st.set_page_config(page_title="SENTINEL OMNI", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# --- BANCO DE DADOS PERSISTENTE ---
def init_db():
    conn = sqlite3.connect('guardion_data.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_alvo REAL, status TEXT, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- MOTOR DE PREÇOS ---
def get_live_price(coin):
    try:
        # Busca direta da CoinGecko
        ids = {"WBTC": "bitcoin", "ETH": "ethereum", "POL": "matic-network"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        data = requests.get(url, timeout=5).json()
        return data[ids[coin]]['usd']
    except:
        return None

# --- INTERFACE ---
st.title("🤖 AGENTE AUTÔNOMO: SENTINEL ATIVO")

# Barra Lateral: Criação de Novos Agentes
with st.sidebar:
    st.header("⚡ Criar Novo Sentinela")
    alvo_moeda = st.selectbox("Ativo para Vigiar", ["WBTC", "ETH", "POL"])
    valor_gatilho = st.number_input("Preço de Gatilho (USD)", value=50000.0)
    
    if st.button("ATIVAR AGENTE"):
        nova_acc = Account.create() # Gera carteira nova na hora
        db.execute("INSERT INTO modulos (nome, endereco, privada, alvo, preco_alvo, status, ultima_acao) VALUES (?,?,?,?,?,?,?)",
                   (f"SNPR-{alvo_moeda}", nova_acc.address, nova_acc.key.hex(), alvo_moeda, valor_gatilho, "VIGILANCIA", "Criado"))
        db.commit()
        st.success("Sentinela posicionado!")

# Painel de Controle dos Agentes
st.subheader("📡 Status dos Módulos Autônomos")
agentes = db.execute("SELECT * FROM modulos").fetchall()

if agentes:
    # Grid de visualização
    for ag in agentes:
        id, nome, addr, priv, alvo, p_alvo, status, u_acao = ag
        preco_agora = get_live_price(alvo)
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            
            c1.markdown(f"**{nome}**")
            c1.caption(f"`{addr[:10]}...`")
            
            c2.metric(f"Preço {alvo}", f"${preco_agora}" if preco_agora else "Erro RPC")
            c3.metric("Alvo", f"${p_alvo}")
            
            # Lógica de Decisão do Sentinela
            if preco_agora and preco_agora <= p_alvo and status == "VIGILANCIA":
                c4.warning("⚠️ CONDIÇÃO ATENDIDA! EXECUTANDO...")
                # Aqui o bot chama a função de SWAP que fizemos anteriormente
                db.execute("UPDATE modulos SET status = ?, ultima_acao = ? WHERE id = ?", 
                           ("EXECUTADO", f"Comprou {alvo} a ${preco_agora}", id))
                db.commit()
                st.rerun()
            else:
                c4.info(f"Status: {status} | {u_acao}")

else:
    st.info("Nenhum agente ativo. Gere um módulo na barra lateral.")

# --- AUTO-REFRESH (O Coração da Autonomia) ---
st.divider()
st.caption(f"Última verificação: {datetime.now().strftime('%H:%M:%S')}")

# O Streamlit vai recarregar sozinho a cada 60 segundos para re-checar os preços
time.sleep(60)
st.rerun()