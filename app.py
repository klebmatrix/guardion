import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, secrets, requests, os
from datetime import datetime

# 1. Configuração e Conexão (RPC estável)
st.set_page_config(page_title="SENTINEL OMNI", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# 2. Banco de Dados com Auto-Reparo (Reset automático em caso de erro)
def init_db():
    db_path = 'guardion_data.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        # Tenta ler a tabela. Se falhar ou estiver incompleta, o except recria.
        conn.execute("SELECT ultima_acao FROM modulos LIMIT 1")
    except:
        st.warning("⚠️ Atualizando estrutura do banco de dados...")
        conn.close()
        if os.path.exists(db_path):
            os.remove(db_path) # Deleta o arquivo velho e problemático
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute('''CREATE TABLE modulos 
                        (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                        alvo TEXT, preco_alvo REAL, status TEXT, ultima_acao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# 3. Motor de Preços (Verifica Bitcoin, Ethereum e Polygon)
def get_live_price(coin):
    try:
        ids = {"WBTC": "bitcoin", "ETH": "ethereum", "POL": "matic-network"}
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=usd"
        data = requests.get(url, timeout=5).json()
        return data[ids[coin]]['usd']
    except:
        return None

# --- INTERFACE PRINCIPAL ---
st.title("🤖 GUARDION SENTINEL | AUTONOMIA TOTAL")

# Barra Lateral: Criação de Novos Agentes
with st.sidebar:
    st.header("⚡ Gerar Agente Autônomo")
    alvo_moeda = st.selectbox("Moeda para Vigiar", ["WBTC", "ETH", "POL"])
    valor_gatilho = st.number_input("Comprar quando o preço for menor que:", value=40000.0)
    
    if st.button("ATIVAR SENTINELA"):
        nova_acc = Account.create() 
        cursor = db.cursor()
        cursor.execute("INSERT INTO modulos (nome, endereco, privada, alvo, preco_alvo, status, ultima_acao) VALUES (?,?,?,?,?,?,?)",
                   (f"SNPR-{alvo_moeda}-{secrets.token_hex(2)}", nova_acc.address, nova_acc.key.hex(), alvo_moeda, valor_gatilho, "VIGILANCIA", "Iniciado"))
        db.commit()
        st.success("Sentinela Criado e Posicionado!")

# 4. Painel de Monitoramento (Onde o robô trabalha)
st.subheader("📡 Status da Rede de Agentes")
cursor = db.cursor()
agentes = cursor.execute("SELECT * FROM modulos").fetchall()



if agentes:
    for ag in agentes:
        id_m, nome, addr, priv, alvo, p_alvo, status, u_acao = ag
        preco_agora = get_live_price(alvo)
        
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            
            col1.markdown(f"**{nome}**")
            col1.caption(f"`{addr[:10]}...`")
            
            col2.metric(f"Preço {alvo}", f"${preco_agora}" if preco_agora else "---")
            col3.metric("Alvo", f"${p_alvo}")
            
            # Lógica do Robô: Se o preço cair, ele executa
            if preco_agora and preco_agora <= p_alvo and status == "VIGILANCIA":
                col4.warning("🚀 CONDIÇÃO ATENDIDA! COMPRANDO...")
                # Aqui o bot executaria o swap real se houvesse saldo
                cursor.execute("UPDATE modulos SET status = ?, ultima_acao = ? WHERE id = ?", 
                               ("EXECUTADO", f"Comprou a ${preco_agora} em {datetime.now().strftime('%H:%M')}", id_m))
                db.commit()
                st.rerun()
            else:
                col4.info(f"Status: {status} | {u_acao}")
else:
    st.info("Nenhum agente em campo. Use a barra lateral para começar.")

# 5. Sistema de Auto-Refresh (Mantém o bot acordado)
st.divider()
st.caption(f"🔄 Última varredura: {datetime.now().strftime('%H:%M:%S')}")

# O robô pisca a tela a cada 60 segundos para reavaliar o mercado
time.sleep(60)
st.rerun()