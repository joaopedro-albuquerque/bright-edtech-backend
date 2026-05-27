from fastapi import FastAPI

from app.api.routers.profile import router as profile_router
from app.api.routers.document import router as document_router

app = FastAPI(
    title="Bright EdTech API",
    description="Backend para orquestração de fluxos de estudos e IA",
    version="0.1.0"
)

app.include_router(profile_router)
app.include_router(document_router)

@app.get("/")
def health_check():
    return {
        "status": "online", 
        "mensagem": "Servidor FastAPI rodando!"
    }