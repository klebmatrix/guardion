import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

PIN_SISTEMA = os.getenv("guardiao", "123456")

# Banco de dados temporário (em memória)
dados_bot = {"status": "OFF", "preference": "YES"}
historico = [
    {"data": "2026-02-03", "mercado": "BTC > 100k", "lado": "YES", "valor": "2.00", "resultado": "WIN"},
    {"data": "2026-02-02", "mercado": "POL Up", "lado": "NO", "valor": "1.50", "resultado": "LOSS"}
]

def logica_robo_decisao(mercado):
    # Aqui entra a inteligência: ele escolhe baseado na sua preferência
    return dados_bot["preference"]

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def validar_login(pin: str = Form(...)):
    if pin == PIN_SISTEMA:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<h1>PIN INCORRETO</h1><a href='/'>Voltar</a>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    mercados = [
        {"id": "m1", "question": "Bitcoin 100k em Fev?", "slug": "btc-100k"},
        {"id": "m2", "question": "Ethereum 5k em Mar?", "slug": "eth-5k"}
    ]
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": "0x...E43E",
        "usdc": "14.44",
        "pol": "1.25",
        "bot": dados_bot,
        "markets": mercados,
        "historico": historico
    })

@app.post("/toggle_bot")
async def atualizar_setup(status: str = Form(...), preference: str = Form(...)):
    global dados_bot
    dados_bot["status"] = status
    dados_bot["preference"] = preference
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)