from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.profile import router as profile_router
from app.api.routers.document import pastas_router, documentos_router, resumos_router

app = FastAPI(
    title="Bright EdTech API",
    description="Backend para orquestração de fluxos de estudos e IA",
    version="0.1.0",
    redirect_slashes=True  
)

origins = [
    "https://brightedtech.com.br",
    "https://www.brightedtech.com.br",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router)
app.include_router(pastas_router)
app.include_router(documentos_router)
app.include_router(resumos_router)

@app.get("/")
def health_check():
    return {
        "status": "online", 
        "mensagem": "Servidor FastAPI rodando!"
    }