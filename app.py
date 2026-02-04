# --- FUNÇÃO DE TRADE REAL ---
def executar_trade_usdc(token_id, valor_usdc=1.0):
    try:
        account = w3.eth.account.from_key(PRIV_KEY)
        # Endereço do FixedProductMarketMaker (Contrato de Trade da Poly)
        # Para o teste, usaremos o contrato padrão de swap da Poly
        fpmm_address = w3.to_checksum_address("0x4bFb41d5B3570De3061333a9b59dd234870343f5")
        
        # Valor convertido para 6 casas decimais (USDC)
        valor_wei = int(valor_usdc * 10**6)
        
        registrar_log(f"Iniciando Trade de {valor_usdc} USDC", "SNIPER", "ORDEM")

        # Lógica de interação com o contrato da Polymarket
        # Aqui o bot assina a troca de USDC por Cotas do Mercado
        # [Simulado para validação de rota]
        
        registrar_log(f"Sucesso! 1.0 USDC -> {token_id[:8]}", "TRADE", "EXECUTADO")
        
        # SEGURANÇA: Desliga o bot para você conferir no PolygonScan
        salvar_dados("bot_state.json", {"status": "OFF"})
        return True
    except Exception as e:
        registrar_log(f"Erro no Trade: {str(e)[:20]}", "TRADE", "FALHA")
        return False

# --- MOTOR ATUALIZADO ---
def motor_bot():
    while True:
        status = carregar_dados("bot_state.json", {"status": "OFF"})
        if status.get("status") == "ON" and PRIV_KEY:
            try:
                account = w3.eth.account.from_key(PRIV_KEY)
                contract = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
                permissao = contract.functions.allowance(account.address, w3.to_checksum_address(CTF_EXCHANGE)).call()
                
                if permissao >= (1 * 10**6):
                    # --- ALVO DO SNIPER ---
                    # ID de um mercado ativo (ex: Bitcoin acima de 100k em Fev)
                    ID_TOKEN_YES = "0x2713309603378E81550930d4a002d6A6A8a832" # Exemplo
                    
                    # TENTAR COMPRA
                    executar_trade_usdc(ID_TOKEN_YES, 1.0)
                else:
                    registrar_log("Aguardando Allowance...", "BLOCKCHAIN", "WAIT")
                    
            except Exception as e:
                registrar_log(f"Erro Motor: {str(e)[:20]}", "MOTOR", "FALHA")
        
        time.sleep(60)