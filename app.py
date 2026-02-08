import streamlit as st
from web3 import Web3
from eth_account import Account

# CONEXÃO ESTÁVEL
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

st.set_page_config(page_title="GUARDION v29.1 - FIXED", layout="wide")

st.title("💰 RESGATE REAL - CORREÇÃO DE CAMPO")

# 1. CARTEIRA QUE RECEBE
st.subheader("🎯 Carteira de Destino (Sua MetaMask)")
# O endereço que você passou: 0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe
carteira_input = st.text_input("Cole seu endereço 0x...", value="0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe")

st.divider()

# 2. CHAVE DO SNIPER
st.subheader("🔑 Chave Privada do Sniper (10.55 POL)")
pk_sniper = st.text_input("Cole a Private Key do Sniper:", type="password")

if st.button("🚀 EXECUTAR SAQUE AGORA", use_container_width=True):
    if not pk_sniper:
        st.error("Insira a Private Key!")
    else:
        try:
            # CORREÇÃO CRITICAL: Transforma o endereço no formato que a rede aceita
            carteira_destino = W3.to_checksum_address(carteira_input)
            
            conta = Account.from_key(pk_sniper)
            saldo_total_wei = W3.eth.get_balance(conta.address)
            
            # Cálculo de Gas
            gas_price = int(W3.eth.gas_price * 1.5)
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
                
                st.success(f"✅ SUCESSO! 10.55 POL ENVIADOS PARA {carteira_destino}")
                st.balloons()
                st.info(f"Hash da Transação: {W3.to_hex(tx_hash)}")
            else:
                st.error("Saldo insuficiente para pagar a taxa de rede (Gas).")
        except Exception as e:
            st.error(f"ERRO NA BLOCKCHAIN: {e}")

st.divider()
st.caption("A rede Polygon exige Checksum Address. O sistema agora faz isso por você.")