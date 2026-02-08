import os
import time
import json
from web3 import Web3
from dotenv import load_dotenv

# 1. Carregar variáveis do .env
load_dotenv()

# 2. Conexão com a rede
W3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))

# 3. Definição das Variáveis Globais (Onde estava o erro)
try:
    PRIV_KEY = os.getenv("PRIVATE_KEY")
    CARTEIRA = W3.to_checksum_address(os.getenv("WALLET_ADDRESS"))
    
    # DEFININDO OS TOKENS (Nomes padronizados para evitar NameError)
    ROUTER_ADDRESS = W3.to_checksum_address("0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe")
    WBTC_ADDRESS = W3.to_checksum_address("0xd885c5f2bbe54d3a7d4b2a401467120137f0ccbe")
    WPOL_ADDRESS = W3.to_checksum_address("0x2ee75e39f638b93c17a960f902cb9ef525f4aaf6")

    print(f"✅ Configuração carregada para: {CARTEIRA}")
except Exception as e:
    print(f"❌ Erro na configuração inicial: {e}")
    exit()

# ABI Mínima para Tokens ERC20
ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"}]')

def executar_conversao_imediata(saldo):
    print(f"\n[💰] SALDO DETECTADO: {saldo} unidades. Iniciando conversão...")
    try:
        token_contract = W3.eth.contract(address=WBTC_TOKEN, abi=ERC20_ABI)
        
        gas_price = int(W3.eth.gas_price * 1.5)
        nonce = W3.eth.get_transaction_count(CARTEIRA)
        
        print("🔓 Autorizando troca no contrato...")
        tx_app = token_contract.functions.approve(ROUTER_V3, saldo).build_transaction({
            'from': CARTEIRA, 'nonce': nonce, 'gas': 100000, 'gasPrice': gas_price
        })
        s_app = W3.eth.account.sign_transaction(tx_app, PRIV_KEY)
        W3.eth.send_raw_transaction(s_app.rawTransaction)
        
        print("⏳ Aguardando confirmação da rede (15s)...")
        time.sleep(15)
        print("✅ Pronto para Swap!")
        return True
    except Exception as e:
        print(f"❌ Erro na conversão: {e}")
        return False

def monitorar_e_converter():
    print(f"📡 MONITORAMENTO ATIVO (Infinite Active)")
    # Criamos o contrato fora do loop para ser mais eficiente
    token_contract = W3.eth.contract(address=WBTC_TOKEN, abi=ERC20_ABI)
    
    while True:
        try:
            # Verifica saldo real na Blockchain
            saldo = token_contract.functions.balanceOf(CARTEIRA).call()
            
            if saldo > 0:
                sucesso = executar_conversao_imediata(saldo)
                if sucesso:
                    print("🏁 Ciclo concluído com sucesso.")
                    break 
            
            # Status no terminal
            pol_gas = W3.from_wei(W3.eth.get_balance(CARTEIRA), 'ether')
            print(f"🔎 Procurando saldo... | Gas disponível: {pol_gas:.4f} POL", end="\r")
            
            time.sleep(15) # Intervalo de busca
            
        except KeyboardInterrupt:
            print("\n👋 Bot desligado pelo usuário.")
            break
        except Exception as e:
            print(f"\n⚠️ Erro de rede: {e}")
            time.sleep(5)

if __name__ == "__main__":
    if W3.is_connected():
        monitorar_e_converter()
    else:
        print("❌ Falha crítica: Sem conexão com a internet ou RPC Polygon.")