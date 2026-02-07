import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, os
import pandas as pd
from datetime import datetime

# 1. Conexão e Banco de Dados
st.set_page_config(page_title="GUARDION OMNI | PERFORMANCE", layout="wide")
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

def init_db():
    conn = sqlite3.connect('guardion_data.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS modulos 
                    (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT, 
                    alvo TEXT, preco_gatilho REAL, preco_compra REAL, lucro_esperado REAL, 
                    stop_loss REAL, status TEXT, ultima_acao TEXT, data_criacao TEXT)''')
    conn.commit()
    return conn

db = init_db()

# --- ABA DE RELATÓRIO E EXPORTAÇÃO ---
st.divider()
st.subheader("📊 Relatório de Performance e Auditoria")

# Busca os dados do banco para o Pandas
query = "SELECT nome, alvo, preco_compra, status, ultima_acao FROM modulos WHERE status IN ('FINALIZADO', 'STOPPED')"
df_historico = pd.read_sql_query(query, sqlite3.connect('guardion_data.db'))

if not df_historico.empty:
    # Exibe a tabela no Dashboard
    st.dataframe(df_historico, use_container_width=True)
    
    # Botão para baixar em Excel/CSV
    csv = df_historico.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 BAIXAR HISTÓRICO PARA EXCEL",
        data=csv,
        file_name=f'guardion_performance_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )
else:
    st.info("Aguardando a conclusão das primeiras operações para gerar o relatório.")

# --- DICA DE SEGURANÇA FINAL ---
with st.expander("🔐 Notas de Segurança do Administrador"):
    st.write("""
    - **Backup:** O arquivo `guardion_data.db` contém suas chaves privadas geradas. Não o compartilhe.
    - **Gas:** Mantenha sempre 1 ou 2 POL em cada carteira ativa para garantir que o Stop Loss ou Take Profit seja executado.
    - **Saque:** Sempre verifique o endereço de destino antes de clicar em 'Retirar Valor'.
    """)



st.caption(f"Sistema Guardion Omni Pro v4.0 | Operando em Ciclo Contínuo")