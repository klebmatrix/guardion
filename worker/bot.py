import os
import asyncio
import httpx
from fastapi import FastAPI
import uvicorn

# Configurações
API_URL = os.getenv("API_URL", "https://guardiao-4tem.onrender.com")
PORT = int(os.getenv("PORT", 10000))

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "operante", "carteira": "E43E", "msg": "Bot rodando liso"}

async def monitoramento():
    """Lógica que roda em segundo plano sem travar a porta"""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Envia sinal de vida para o seu painel
                await client.get(f"{API_URL}/api/registrar_operacao", params={
                    "msg": "BOT ONLINE - MONITORANDO 14.44 USDC",
                    "tipo": "win"
                })
                print("✅ Log enviado ao site principal.")
            except Exception as e:
                print(f"❌ Erro ao reportar: {e}")
            
            await asyncio.sleep(45) # Espera 45 seg para o próximo sinal

@app.on_event("startup")
async def startup_event():
    # Inicia o loop de monitoramento assim que o servidor ligar
    asyncio.create_task(monitoramento())

if __name__ == "__main__":
    # Roda o servidor na porta que o Render exige
    uvicorn.run(app, host="0.0.0.0", port=PORT)