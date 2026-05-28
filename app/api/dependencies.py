# app/api/dependencies.py
from fastapi import Depends
from app.core.database import get_db_connection
from app.repositories.DocumentRepository import DocumentRepository
from app.repositories.ProfileRepository import ProfileRepository
from app.repositories.DashboardRepository import DashboardRepository
from app.services.DocumentGeneratorService import DocumentGeneratorService
from app.services.ProfileService import ProfileService
from app.services.DashboardService import DashboardService

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# Profile 
def get_profile_repository(conn = Depends(get_db)) -> ProfileRepository:
    return ProfileRepository(conn)

def get_profile_service(repo: ProfileRepository = Depends(get_profile_repository)) -> ProfileService:
    return ProfileService(repo)

# Document
def get_document_repository(conn = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(conn)

def get_document_generator_service(repo: DocumentRepository = Depends(get_document_repository)) -> DocumentGeneratorService:
    return DocumentGeneratorService(repo)

# Dashboard
def get_dashboard_repository(conn = Depends(get_db)) -> DashboardRepository:
    return DashboardRepository(conn)

def get_dashboard_service(repo: DashboardRepository = Depends(get_dashboard_repository)) -> DashboardService:
    return DashboardService(repo)
