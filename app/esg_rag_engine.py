import os
from pathlib import Path
from dotenv import load_dotenv

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain

# === Configurações ===

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega as variáveis do .env
load_dotenv(BASE_DIR / ".env")

# Chave da OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY não foi definida no .env")

os.environ["OPENAI_API_KEY"] = api_key
print("✅ API Key carregada com sucesso!")

# Modelo (padrão gpt-3.5-turbo)
model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Diretório de uploads
UPLOADS_DIR = BASE_DIR / "uploads"

# Caminho para os arquivos de diretrizes
diretrizes_esg_path = BASE_DIR / "diretrizes_esg.txt"
diretrizes_iso_path = BASE_DIR / "diretrizes_iso.txt"

# === Funções principais ===

def carregar_e_dividir_pdf(caminho_pdf: Path):
    """Carrega e divide o PDF em pedaços menores (chunks)."""
    loader = PyPDFLoader(str(caminho_pdf))
    documentos = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    return splitter.split_documents(documentos)

def carregar_diretrizes() -> str:
    """Carrega e junta as diretrizes ESG e ISO em um único texto."""
    if not diretrizes_esg_path.exists():
        raise FileNotFoundError("Arquivo 'diretrizes_esg.txt' não encontrado.")
    if not diretrizes_iso_path.exists():
        raise FileNotFoundError("Arquivo 'diretrizes_iso.txt' não encontrado.")

    with open(diretrizes_esg_path, "r", encoding="utf-8") as f:
        esg = f.read()

    with open(diretrizes_iso_path, "r", encoding="utf-8") as f:
        iso = f.read()

    return f"DIRETRIZES ESG:\n{esg}\n\nDIRETRIZES ISO:\n{iso}"

def indexar_chunks(chunks):
    """Cria um índice vetorial FAISS a partir dos chunks."""
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(chunks, embeddings)

def recuperar_trechos_relevantes(index, pergunta: str):
    """Recupera os trechos mais relevantes usando busca semântica."""
    return index.similarity_search(pergunta, k=5)

def responder_pergunta(com_trechos, pergunta: str, diretrizes: str):
    """Usa LangChain + OpenAI para responder com base nos trechos e diretrizes."""
    llm = ChatOpenAI(temperature=0.2, model_name=model_name)

    prompt_inicial = f"""
Você é um auditor especializado em ESG e normas ISO. 
Use as diretrizes abaixo para avaliar os documentos:
---
{diretrizes}
---
Com base nisso, responda à seguinte pergunta:
"""

    chain = load_qa_chain(llm, chain_type="stuff", prompt=None)
    resposta = chain.run(input_documents=com_trechos, question=prompt_inicial + pergunta)
    return resposta.strip()

def analyze_document_with_esg_guidelines(file_path: str, pergunta: str) -> dict:
    """Fluxo completo RAG: indexação + recuperação + resposta"""
    caminho_completo = UPLOADS_DIR / file_path
    if not caminho_completo.exists():
        return {
            "pergunta": pergunta,
            "resposta": f"<strong>Erro:</strong> Arquivo '{file_path}' não encontrado."
        }

    try:
        print(f"📄 Indexando documento: {file_path}")
        chunks = carregar_e_dividir_pdf(caminho_completo)
        index = indexar_chunks(chunks)
        trechos = recuperar_trechos_relevantes(index, pergunta)
        diretrizes = carregar_diretrizes()
        resposta = responder_pergunta(trechos, pergunta, diretrizes)

        return {
            "pergunta": pergunta,
            "resposta": (
                f"<strong>Pergunta:</strong> {pergunta}<br>"
                f"<strong>Arquivo analisado:</strong> {file_path}<br><br>"
                f"<strong>Resultado:</strong><br>{resposta}"
            )
        }

    except Exception as e:
        print(f"[Erro geral] {e}")
        return {
            "pergunta": pergunta,
            "resposta": (
                "<strong>Erro:</strong> Ocorreu uma falha ao processar sua solicitação. "
                "Verifique se os arquivos estão corretos ou tente novamente mais tarde."
            )
        }
