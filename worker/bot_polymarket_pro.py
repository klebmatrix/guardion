import os, asyncio, json, requests, uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from web3 import Web3
from fpdf import FPDF
from io import BytesIO
import base64

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAÇÕES REAIS ---
WALLET = "0x9BD6A55e48Ec5cDf165A0051E030Cd1419EbE43E"
PRIV_KEY = os.getenv("private_key")
RPC_POLYGON = "https://polygon-rpc.com"

USDC_NATIVO = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ABI_USDC = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

w3 = Web3(Web3.HTTPProvider(RPC_POLYGON))
bot_config = {"status": "OFF"}

def registrar_log(mensagem, lado="AUTO"):
    """Registra operações do bot em arquivo JSON"""
    try:
        agora = datetime.now().strftime("%d/%m %H:%M:%S")
        log = {"data": agora, "mercado": mensagem, "lado": lado, "resultado": "OK"}
        dados = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f: 
                dados = json.load(f)
        dados.insert(0, log)
        with open("logs.json", "w") as f: 
            json.dump(dados[:50], f)  # Aumentado para 50 registros
        return dados
    except: 
        return []

def gerar_pdf_relatorio():
    """Gera relatório em PDF com todos os logs de operações"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Cabeçalho
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "RELATORIO DE OPERACOES - SNIPER BOT", ln=True, align="C")
        
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 5, f"Wallet: {WALLET}", ln=True)
        pdf.cell(0, 5, f"Data do Relatorio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
        pdf.ln(5)
        
        # Carrega logs
        logs = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f:
                logs = json.load(f)
        
        # Tabela de operações
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(40, 8, "Data/Hora", border=1)
        pdf.cell(80, 8, "Mercado", border=1)
        pdf.cell(40, 8, "Lado", border=1)
        pdf.cell(30, 8, "Status", border=1, ln=True)
        
        pdf.set_font("helvetica", "", 9)
        for log in logs:
            pdf.cell(40, 8, log.get("data", ""), border=1)
            mercado = log.get("mercado", "")[:25]
            pdf.cell(80, 8, mercado, border=1)
            pdf.cell(40, 8, log.get("lado", ""), border=1)
            pdf.cell(30, 8, log.get("resultado", ""), border=1, ln=True)
        
        pdf.ln(5)
        
        # Resumo
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, "RESUMO", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 6, f"Total de Operacoes: {len(logs)}", ln=True)
        pdf.cell(0, 6, f"Status do Bot: {bot_config['status']}", ln=True)
        
        # Retorna como bytes
        return pdf.output()
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        return None

# --- O CÉREBRO DO BOT (DECISÃO AUTÓNOMA) ---
async def sniper_loop():
    """Loop principal do bot que monitora e executa operações"""
    while True:
        if bot_config["status"] == "ON" and PRIV_KEY:
            try:
                # 1. SCANNER DE MERCADO REAL
                res = requests.get("https://clob.polymarket.com/markets", timeout=10)
                mercado = res.json()[0]
                pergunta = mercado.get('question', 'Polymarket')[:30]
                
                # 2. IA DE DECISÃO
                decisao = "YES"
                
                # 3. LOG DA OPERAÇÃO
                registrar_log(f"Sniper: {pergunta}", decisao)
                
            except Exception as e:
                registrar_log(f"Erro IA: {str(e)[:20]}", "ERRO")
        
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup(): 
    """Inicia o loop do bot ao iniciar a aplicação"""
    asyncio.create_task(sniper_loop())

# --- DASHBOARD ---
@app.get("/dashboard", response_class=HTMLResponse)
async def painel(request: Request):
    """Exibe o painel de controle com dados da carteira e logs"""
    try:
        pol = w3.from_wei(w3.eth.get_balance(WALLET), 'ether')
        c1 = w3.eth.contract(address=w3.to_checksum_address(USDC_NATIVO), abi=json.loads(ABI_USDC))
        c2 = w3.eth.contract(address=w3.to_checksum_address(USDC_BRIDGED), abi=json.loads(ABI_USDC))
        u1 = c1.functions.balanceOf(WALLET).call() / 10**6
        u2 = c2.functions.balanceOf(WALLET).call() / 10**6
        usdc_final = max(u1, u2)
    except: 
        pol, usdc_final = 0.0, 0.0

    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f: 
            logs = json.load(f)

    # Estatísticas
    total_ops = len(logs)
    ops_yes = len([l for l in logs if l.get("lado") == "YES"])
    ops_no = len([l for l in logs if l.get("lado") == "NO"])
    ops_erro = len([l for l in logs if l.get("lado") == "ERRO"])

    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "wallet": WALLET, 
        "usdc": f"{usdc_final:.2f}",
        "pol": f"{pol:.2f}", 
        "bot": bot_config, 
        "historico": logs,
        "total_ops": total_ops,
        "ops_yes": ops_yes,
        "ops_no": ops_no,
        "ops_erro": ops_erro
    })

@app.post("/toggle_bot")
async def toggle(status: str = Form(...)):
    """Alterna o status do bot (ON/OFF)"""
    bot_config["status"] = status
    registrar_log(f"Bot em {status}", "SISTEMA")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/gerar_relatorio")
async def gerar_relatorio():
    """Gera e retorna um PDF com o relatório de operações"""
    pdf_bytes = gerar_pdf_relatorio()
    if pdf_bytes:
        return FileResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            filename=f"relatorio_sniper_{datetime.now().strftime('%d_%m_%Y_%H%M%S')}.pdf"
        )
    return {"erro": "Não foi possível gerar o PDF"}

@app.get("/api/stats")
async def obter_stats():
    """API que retorna estatísticas em JSON para gráficos"""
    logs = []
    if os.path.exists("logs.json"):
        with open("logs.json", "r") as f:
            logs = json.load(f)
    
    return {
        "total": len(logs),
        "yes": len([l for l in logs if l.get("lado") == "YES"]),
        "no": len([l for l in logs if l.get("lado") == "NO"]),
        "erro": len([l for l in logs if l.get("lado") == "ERRO"])
    }

@app.get("/")
async def home(request: Request): 
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/entrar")
async def login(pin: str = Form(...)):
    """Valida o PIN de acesso"""
    if pin == os.getenv("guardiao", "123456"): 
        return RedirectResponse(url="/dashboard", status_code=303)
    return "ERRO"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
