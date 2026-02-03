import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Busca o PIN que você salvou no Render (variável: guardiao)
PIN_SISTEMA = os.getenv("guardiao")

@app.get("/", response_class=HTMLResponse)
async def tela_login(request: Request):
    # 1. BUSCA A TELA DE LOGIN
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def entrar(pin: str = Form(...)):
    # 2. VALIDA O PIN
    if pin == PIN_SISTEMA:
        # 3. SE OK, VAI PARA AS OPERAÇÕES (DASHBOARD)
        return RedirectResponse(url="/operacoes", status_code=303)
    return HTMLResponse("<h1>PIN INCORRETO</h1><a href='/'>Tentar novamente</a>")

@app.get("/operacoes", response_class=HTMLResponse)
async def dashboard(request: Request):
    # 4. EXIBE O DASHBOARD REAL
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "saldo": "14.44 USDC",
        "carteira": "E43E"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)