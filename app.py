import streamlit as st
from web3 import Web3
from eth_account import Account
import sqlite3, time

# --- CONEXÃO REAL (REDE POLYGON) ---
RPC_POLYGON = "https://polygon-rpc.com"
W3 = Web3(Web3.HTTPProvider(RPC_POLYGON))

st.set_page_config(page_title="GUARDION v21.0 - CASH OUT", layout="wide")

# --- DATABASE ---
db = sqlite3.connect('guardion_final_real.db', check_same_thread=False)
db.execute('''CREATE TABLE IF NOT EXISTS snipers 
            (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, privada TEXT)''')
db.commit()

# --- FUNÇÃO DE SAQUE "MATA-TUDO" ---
def sacar_agora_real(privada_origem, carteira_destino):
    try:
        conta = Account.from_key(privada_origem)
        saldo_wei = W3.eth.get_balance(conta.address)
        
        # Pega o preço do gás e joga 20% em cima para garantir que a rede aceite
        gas_price = int(W3.eth.gas_price * 1.2)
        taxa_transferencia = gas_price * 21000
        
        valor_liquido = saldo_wei - taxa_transferencia
        
        if valor_liquido > 0:
            tx = {
                'nonce': W3.eth.get_transaction_count(conta.address),
                'to': carteira_destino,
                'value': valor_liquido,
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': 137
            }
            assinada = W3.eth.account.sign_transaction(tx, privada_origem)
            hash_tx = W3.eth.send_raw_transaction(assinada.raw_transaction)
            return f"✅ SUCESSO: {W3.to_hex(hash_tx)[:15]}..."
        else:
            return "❌ SALDO INSUFICIENTE PARA TAXA"
    except Exception as e:
        return f"❌ ERRO: {str(e)}"

# --- INTERFACE DE GUERRA ---
st.title("🛡️ GUARDION v21.0 | SAQUE REAL IMEDIATO")
st.warning("MODO REAL ATIVO: Certifique-se de que sua carteira de destino está correta.")

with st.sidebar:
    st.header("🔑 CONFIGURAÇÃO")
    carteira_mestra = st.text_input("SUA CARTEIRA (Para receber o dinheiro):")
    if st.button("🔄 GERAR 10 CARTEIRAS"):
        db.execute("DELETE FROM snipers")
        for i in range(10):
            acc = Account.create()
            db.execute("INSERT INTO snipers VALUES (?,?,?,?)", (i, f"SNIPER-{i+1:02d}", acc.address, acc.key.hex()))
        db.commit()
        st.rerun()

# --- PAINEL DE RETIRADA ---
agentes = db.execute("SELECT * FROM snipers").fetchall()

if not agentes:
    st.info("Clique em 'GERAR 10 CARTEIRAS' para começar.")
else:
    st.subheader("💰 SALDO DOS SNIPERS EM TEMPO REAL")
    
    # Criar uma tabela visual de saque
    for a in agentes:
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            # Checa saldo on-chain
            try:
                saldo = W3.from_wei(W3.eth.get_balance(a[2]), 'ether')
            except:
                saldo = 0.0
            
            with col1:
                st.write(f"**{a[1]}**")
            with col2:
                st.write(f"Endereço: `{a[2]}`")
                if saldo > 0:
                    st.success(f"SALDO: {saldo:.4f} POL")
                else:
                    st.error("SALDO: 0.00 POL")
            with col3:
                # BOTÃO DE RETIRADA INDIVIDUAL
                if st.button(f"RETIRAR AGORA", key=f"saque_{a[0]}"):
                    if not carteira_mestra:
                        st.error("Preencha a carteira de destino!")
                    else:
                        res = sacar_agora_real(a[3], carteira_mestra)
                        st.write(res)

    st.divider()
    if st.button("🚀 SAQUE TOTAL (RETIRAR DE TODOS DE UMA VEZ)", use_container_width=True):
        if not carteira_mestra:
            st.error("Defina a carteira mestra!")
        else:
            for a in agentes:
                res = sacar_agora_real(a[3], carteira_mestra)
                st.toast(f"{a[1]}: {res}")
                time.sleep(1) # Delay para evitar bloqueio da rede
            st.success("Operação de Saque em Massa finalizada!")

time.sleep(10)
st.rerun()