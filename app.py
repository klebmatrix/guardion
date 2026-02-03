import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Sua regra: variáveis em minúsculas no Render
PIN_SISTEMA = os.getenv("guardiao", "123456")

# Simulação de dados para o seu HTML mobile
dados_bot = {"status": "OFF", "preference": "YES"}
mercados_exemplo = [
    {"id": "1", "question": "O Bitcoin atinge 100k em Fevereiro?", "slug": "btc-100k-feb"},
    {"id": "2", "question": "POL vai subir 20% esta semana?", "slug": "pol-up-20"}
]

@app.get("/", response_class=HTMLResponse)
async def tela_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def entrar(pin: str = Form(...)):
    if pin == PIN_SISTEMA:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<h1>PIN INCORRETO</h1><a href='/'>Tentar novamente</a>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": "0x...E43E", # Sua carteira
        "usdc": "14.44",        # Seu saldo
        "pol": "1.25",          # Saldo de gás
        "bot": dados_bot,
        "markets": mercados_exemplo,
        "aviso": "Sistema Operacional Guardião Pronto para Trades."
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)