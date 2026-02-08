import streamlit as st
from web3 import Web3
from eth_account import Account

# Conexão com RPC alternativa (mais estável)
W3 = Web3(Web3.HTTPProvider("https://polygon-bor-rpc.publicnode.com"))

st.title("🚨 CORREÇÃO DE FLUXO E RESGATE")

# 1. SUA CARTEIRA (DESTINO)
# Já estou aplicando a correção automática (to_checksum_address)
meu_destino = "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"
try:
    carteira_correta = W3.to_checksum_address(meu_destino.strip())
    st.success(f"Destino Validado: {carteira_correta}")
except:
    st.error("Erro fatal no endereço de destino. Verifique os caracteres.")

st.divider()

# 2. ENTRADA DA CHAVE DO SNIPER
st.subheader("🔑 Chave Privada do Sniper que tem os 10.55 POL")
pk_resgate = st.text_input("Cole a Private Key aqui:", type="password")

if st.button("🚀 FORÇAR SAQUE AGORA"):
    if pk_resgate:
        try:
            # Limpa espaços e valida a chave
            pk_limpa = pk_resgate.strip()
            conta_origem = Account.from_key(pk_limpa)
            
            # Consulta saldo real
            saldo_wei = W3.eth.get_balance(conta_origem.address)
            saldo_pol = W3.from_wei(saldo_wei, 'ether')
            
            st.write(f"Verificando Sniper: `{conta_origem.address}`")
            st.write(f"Saldo encontrado: **{saldo_pol} POL**")
            
            if saldo_wei > 0:
                # Configuração de Gás Turbo
                gas_price = int(W3.eth.gas_price * 2.0)
                taxa = gas_price * 21000
                
                tx = {
                    'nonce': W3.eth.get_transaction_count(conta_origem.address),
                    'to': carteira_correta,
                    'value': saldo_wei - taxa,
                    'gas': 21000,
                    'gasPrice': gas_price,
                    'chainId': 137
                }
                
                signed = W3.eth.account.sign_transaction(tx, pk_limpa)
                tx_hash = W3.eth.send_raw_transaction(signed.raw_transaction)
                
                st.balloons()
                st.success(f"✅ DINHEIRO ENVIADO! Hash: {W3.to_hex(tx_hash)}")
                st.info("Verifique sua MetaMask na rede Polygon.")
            else:
                st.error("Este Sniper está com saldo 0. Verifique se enviou o POL para o endereço correto.")
        except Exception as e:
            st.error(f"Erro na transação: {e}")