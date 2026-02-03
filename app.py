from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "OpenClaw Local Ativo", "saldo_alvo": "14.44 USDC"}