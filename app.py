import streamlit as st
from web3 import Web3
from eth_account import Account
import time

# USANDO UM RPC DIFERENTE PARA GARANTIR
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v30.0 - FORCE PUSH", layout="wide")

st.title("🛡️ RASTREADOR DE MOVIMENTAÇÃO REAL")

# DADOS DE SEGURANÇA
st.sidebar.header("🎯 DESTINO")
carteira_destino = st.sidebar.text_input("Sua MetaMask:", value="0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe")

st.divider()

# ENTRADA DE DADOS PARA O RESGATE
col1, col2 = st.columns(2)
with col1:
    pk_sniper = st.text_input("🔑 Private Key do Sniper:", type="password", help="A chave de onde está o 10.55 POL")
with col2:
    st.info("O sistema vai tentar forçar a saída do saldo agora.")

if st.button("🚀 FORÇAR SAÍDA DOS 10.55 POL AGORA", use_container_width=True):
    try:
        dest_checksum = W3.to_checksum_address(carteira_destino)
        conta = Account.from_key(pk_sniper)
        saldo_wei = W3.eth.get_balance(conta.address)
        
        # Aumentando o Gas Price para Prioridade Máxima (Turbo)
        gas_price_atual = W3.eth.gas_price
        gas_price_turbo = int(gas_price_atual * 2.5) # 2.5x mais rápido
        custo_gas = gas_price_turbo * 21000
        
        valor_enviar = saldo_wei - custo_gas
        
        if valor_enviar > 0:
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address, 'pending'), # Pega inclusive as travadas
                'to': dest_checksum,
                'value': valor_enviar,
                'gas': 21000,
                'gasPrice': gas_price_turbo,
                'chainId': 137
            }
            
            signed = W3.eth.account.sign_transaction(tx, pk_sniper)
            tx_hash = W3.eth.send_raw_transaction(signed.raw_transaction)
            
            hash_hex = W3.to_hex(tx_hash)
            st.success("🔥 TRANSAÇÃO LANÇADA COM PRIORIDADE MÁXIMA!")
            st.link_button("➡️ VER DINHEIRO MOVENDO NO POLYGONSCAN", f"https://polygonscan.com/tx/{hash_hex}")
            st.write(f"Valor: {W3.from_wei(valor_enviar, 'ether')} POL")
        else:
            st.error("Saldo insuficiente para cobrir o Gás Turbo.")
    except Exception as e:
        st.error(f"Erro: {e}")

st.divider()
st.subheader("🕵️ POR QUE PAROU?")
st.write("1. **Transação Pendente:** Clique no botão acima para ver se já existe algo no seu endereço.")
st.write("2. **Sincronização:** A MetaMask às vezes demora a mostrar. Verifique no PolygonScan.")
st.write("3. **Sem Movimentação Visual:** Se o robô não tem saldo, ele não faz o 'teatro' do lucro subindo.")