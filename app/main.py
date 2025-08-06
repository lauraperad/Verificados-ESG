import os
import shutil
from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.esg_rag_engine import analyze_document_with_esg_guidelines

# Diretórios base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Garante que as pastas necessárias existam
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Instância do app FastAPI
app = FastAPI()

# Middleware para CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, use domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Página inicial
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Rota para análise ESG
@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, arquivo: UploadFile, pergunta: str = Form(...)):
    filename = os.path.basename(arquivo.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)

    try:
        # Salva o arquivo
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)

        # Chama a função de análise (RAG)
        resultado = analyze_document_with_esg_guidelines(filename, pergunta)

    except Exception as e:
        print(f"[Erro no backend] {e}")
        resultado = {
            "pergunta": pergunta,
            "resposta": (
                "<strong>Erro:</strong> Ocorreu uma falha ao processar sua solicitação. "
                "Verifique se os arquivos estão corretos ou tente novamente mais tarde."
            )
        }

    # Retorna para a mesma página com a resposta
    return templates.TemplateResponse("index.html", {
        "request": request,
        "pergunta": resultado["pergunta"],
        "resposta": resultado["resposta"],
        "arquivo": filename
    })
