import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configurações de Segurança
PIN_SISTEMA = os.getenv("guardiao", "123456")

# Estado do Sistema (Simulando um Banco de Dados)
estado = {
    "bot": {"status": "OFF", "preference": "YES"},
    "saldo": {"usdc": 14.44, "pol": 1.25, "wallet": "0x...E43E"},
    "historico": [
        {"data": "2026-02-03 14:20", "mercado": "BTC > 100k", "lado": "YES", "valor": "1.00", "resultado": "WIN"},
        {"data": "2026-02-03 15:10", "mercado": "POL Volatility", "lado": "NO", "valor": "0.50", "resultado": "WAIT"}
    ]
}

# --- Lógica Profissional do Bot ---
def executar_estrategia_guardiao():
    """
    Simula a decisão do bot baseada na preferência do usuário 
    e na leitura de 'confiança' do mercado.
    """
    if estado["bot"]["status"] == "ON":
        # Aqui o bot decidiria o valor baseado em % da banca (Ex: 5%)
        valor_operacao = round(estado["saldo"]["usdc"] * 0.05, 2)
        decisao = estado["bot"]["preference"]
        
        # Simula o registro automático
        nova_op = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mercado": "Auto-Scanner Polymarket",
            "lado": decisao,
            "valor": str(valor_operacao),
            "resultado": "OPEN"
        }
        estado["historico"].insert(0, nova_op)

# --- Rotas do Servidor ---

@app.get("/", response_class=HTMLResponse)
async def login_view(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def autenticar(pin: str = Form(...)):
    if pin == PIN_SISTEMA:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse("<h1>ACESSO NEGADO</h1><a href='/'>Tentar Novamente</a>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wallet": estado["saldo"]["wallet"],
        "usdc": estado["saldo"]["usdc"],
        "pol": estado["saldo"]["pol"],
        "bot": estado["bot"],
        "historico": estado["historico"][:5] # Mostra os 5 últimos
    })

@app.post("/toggle_bot")
async def atualizar_config(status: str = Form(...), preference: str = Form(...)):
    estado["bot"]["status"] = status
    estado["bot"]["preference"] = preference
    
    if status == "ON":
        executar_estrategia_guardiao() # Dispara a lógica ao ligar
        
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)