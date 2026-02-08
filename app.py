import streamlit as st
from web3 import Web3
from eth_account import Account

# CONEXÃO ESTÁVEL
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v29.0 - CASH OUT", layout="wide")

st.title("💰 RESGATE DE FUNDOS REAIS (POL)")

# 1. CARTEIRA QUE RECEBE
st.subheader("🎯 Carteira de Destino (Sua MetaMask)")
carteira_destino = st.text_input("Cole seu endereço 0x...", placeholder="0x...")

st.divider()

# 2. CHAVE DO SNIPER QUE TEM OS 10.55 POL
st.subheader("🔑 Chave Privada do Sniper")
pk_sniper = st.text_input("Cole a Private Key do Sniper com saldo:", type="password")

if st.button("🚀 SACAR 10.55 POL AGORA", use_container_width=True):
    if not W3.is_address(carteira_destino):
        st.error("Endereço de destino inválido!")
    elif not pk_sniper:
        st.error("Insira a Private Key!")
    else:
        try:
            conta = Account.from_key(pk_sniper)
            saldo_total_wei = W3.eth.get_balance(conta.address)
            
            # Cálculo agressivo de Gas para não travar
            gas_price = int(W3.eth.gas_price * 1.3)
            gas_limit = 21000
            custo_gas = gas_price * gas_limit
            
            valor_saque = saldo_total_wei - custo_gas
            
            if valor_saque > 0:
                tx = {
                    'nonce': W3.eth.get_transaction_count(conta.address),
                    'to': carteira_destino,
                    'value': valor_saque,
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'chainId': 137
                }
                
                signed = W3.eth.account.sign_transaction(tx, pk_sniper)
                tx_hash = W3.eth.send_raw_transaction(signed.raw_transaction)
                
                st.success("✅ SUCESSO! O DINHEIRO ESTÁ A CAMINHO.")
                st.balloons()
                st.info(f"Hash da Transação: {W3.to_hex(tx_hash)}")
                st.write(f"Valor enviado: {W3.from_wei(valor_saque, 'ether')} POL")
            else:
                st.error("Saldo insuficiente para pagar a taxa de rede.")
        except Exception as e:
            st.error(f"ERRO NA BLOCKCHAIN: {e}")

st.divider()
st.caption("Certifique-se de estar na rede Polygon na sua MetaMask para ver o saldo cair.")