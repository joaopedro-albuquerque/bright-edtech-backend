from fastapi import Depends
from app.repositories.ProfileRepository import ProfileRepository
from app.core.database import get_db_connection

def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_profile_repo(conn = Depends(get_db)) -> ProfileRepository:
    return ProfileRepository(conn)