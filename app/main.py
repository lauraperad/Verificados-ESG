from fastapi import FastAPI, UploadFile, Form, Request, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid

from app.esg_rag_engine import analyze_document_with_esg_guidelines

# Inicializa a aplicação
app = FastAPI()

# ✅ MONTAR arquivos estáticos corretamente (antes das rotas)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, use domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretórios de templates e uploads
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Página inicial
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Upload e análise do arquivo
@app.post("/upload")
async def upload(
    request: Request,
    arquivo: UploadFile = File(...),
    pergunta: str = Form(...)
):
    try:
        # Gera nome de arquivo único
        filename = f"{uuid.uuid4()}_{arquivo.filename}"
        caminho = os.path.join(UPLOAD_DIR, filename)

        # Salva o arquivo localmente
        with open(caminho, "wb") as f:
            shutil.copyfileobj(arquivo.file, f)

        # Analisa com ESG
        resultado = analyze_document_with_esg_guidelines(filename, pergunta)

        return templates.TemplateResponse("resultado.html", {
            "request": request,
            "pergunta": resultado["pergunta"],
            "resposta": resultado["resposta"]
        })

    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": str(e)
        })
