import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Sua regra: variável em minúsculas
PIN_SISTEMA = os.getenv("guardiao", "123456")

# Dados voláteis para o dashboard funcionar
dados_bot = {"status": "OFF", "preference": "YES"}
mercados = [
    {"id": "1", "question": "Bitcoin acima de 100k?", "slug": "btc-100k", "id": "m1"},
    {"id": "2", "question": "POL sobe hoje?", "slug": "pol-up", "id": "m2"}
]

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
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": "0x...E43E",
        "usdc": "14.44",
        "pol": "1.25",
        "bot": dados_bot,
        "markets": mercados
    })

@app.post("/toggle_bot")
async def atualizar_setup(status: str = Form(...), preference: str = Form(...)):
    global dados_bot
    dados_bot["status"] = status
    dados_bot["preference"] = preference
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/trade")
async def realizar_trade(market_id: str = Form(...), amount: float = Form(...), side: str = Form(...)):
    print(f"Trade recebido: {amount} USDC no lado {side}")
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)