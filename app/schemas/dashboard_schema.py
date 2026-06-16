from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class FlashcardItem(BaseModel):
    id: UUID
    titulo: str
    criado_em: datetime
    
    model_config = {"from_attributes": True}

class ResumoItem(BaseModel):
    id: UUID
    nome: str
    criado_em: datetime
    
    model_config = {"from_attributes": True}

class QuizItem(BaseModel):
    id: UUID
    titulo: str
    criado_em: datetime
    
    model_config = {"from_attributes": True}

class DashboardResponse(BaseModel):
    ultimos_flashcards: list[FlashcardItem]
    ultimos_resumos: list[ResumoItem]
    ultimos_quizzes: list[QuizItem]
    total_flashcards: int
    total_resumos: int
    total_quizzes: int
