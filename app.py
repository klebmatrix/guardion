import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time, requests, os

# --- CONEXÃO E SEGURANÇA ---
w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.publicnode.com"))

# A Chave Mestre deve estar no arquivo .streamlit/secrets.toml como PK_MESTRE = "sua_chave"
PK_MESTRE = st.secrets.get("PK_MESTRE")

def auto_abastecer(endereco_agente):
    if not PK_MESTRE:
        return # Sem chave mestre, não há como abastecer sozinho
        
    try:
        acc_mestre = Account.from_key(PK_MESTRE)
        saldo_agente = w3.eth.get_balance(endereco_agente)
        limite_minimo = w3.to_wei(0.1, 'ether') # 0.1 POL
        
        if saldo_agente < limite_minimo:
            st.toast(f"⛽ Abastecendo agente {endereco_agente[:6]}...")
            
            tx = {
                'nonce': w3.eth.get_transaction_count(acc_mestre.address),
                'to': endereco_agente,
                'value': w3.to_wei(0.5, 'ether'), # Envia 0.5 POL
                'gas': 21000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 137
            }
            signed = w3.eth.account.sign_transaction(tx, PK_MESTRE)
            w3.eth.send_raw_transaction(signed.raw_transaction)
            return True
    except:
        return False

# --- NO LOOP PRINCIPAL DO SEU CÓDIGO ---
# (Dentro do loop que percorre os agentes)

for ag in agentes:
    # ... código de monitoramento de preço ...
    
    # VERIFICAÇÃO AUTOMÁTICA DE COMBUSTÍVEL
    if ag[9] != 'FINALIZADO': # ag[9] é o status
        auto_abastecer(ag[2]) # ag[2] é o endereço do agente