from uuid import UUID

from app.core.exceptions import DashboardDatabaseError

class DashboardRepository:
    def __init__(self, conn):
        self.conn = conn

    def buscar_ultimos_flashcards(self, usuario_id: UUID, limit: int = 5) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, titulo, criado_em
                    FROM flashcards
                    WHERE usuario_id = %s
                    ORDER BY criado_em DESC
                    LIMIT %s;
                """
                cursor.execute(query, (usuario_id, limit))
                return cursor.fetchall()
        except Exception as e:
            raise DashboardDatabaseError("Erro no banco de dados ao buscar os últimos flashcards.") from e

    def buscar_ultimos_resumos(self, usuario_id: UUID, limit: int = 5) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, titulo AS nome, criado_em
                    FROM resumos
                    WHERE usuario_id = %s
                    ORDER BY criado_em DESC
                    LIMIT %s;
                """
                cursor.execute(query, (usuario_id, limit))
                return cursor.fetchall()
        except Exception as e:
            raise DashboardDatabaseError("Erro no banco de dados ao buscar os últimos resumos.") from e

    def buscar_ultimos_quizzes(self, usuario_id: UUID, limit: int = 5) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, titulo, criado_em
                    FROM quizzes
                    WHERE usuario_id = %s
                    ORDER BY criado_em DESC
                    LIMIT %s;
                """
                cursor.execute(query, (usuario_id, limit))
                return cursor.fetchall()
        except Exception as e:
            raise DashboardDatabaseError("Erro no banco de dados ao buscar os últimos quizzes.") from e

    def buscar_documentos_recentes(self, usuario_id: UUID, limit: int = 10) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, nome, criado_em
                    FROM documentos
                    WHERE usuario_id = %s
                    ORDER BY criado_em DESC
                    LIMIT %s;
                """
                cursor.execute(query, (usuario_id, limit))
                return cursor.fetchall()
        except Exception as e:
            raise DashboardDatabaseError("Erro no banco de dados ao buscar documentos recentes.") from e

    def contar_total_flashcards(self, usuario_id: UUID) -> int:
        try:
            with self.conn.cursor() as cursor:
                query = "SELECT COUNT(*) as total FROM flashcards WHERE usuario_id = %s;"
                cursor.execute(query, (usuario_id,))
                result = cursor.fetchone()
                return result['total'] if result else 0
        except Exception as e:
            raise DashboardDatabaseError("Erro no banco de dados ao contar o total de flashcards.") from e

    def contar_total_resumos(self, usuario_id: UUID) -> int:
        try:
            with self.conn.cursor() as cursor:
                query = "SELECT COUNT(*) as total FROM resumos WHERE usuario_id = %s;"
                cursor.execute(query, (usuario_id,))
                result = cursor.fetchone()
                return result['total'] if result else 0
        except Exception as e:
            raise DashboardDatabaseError("Erro no banco de dados ao contar o total de resumos.") from e

    def contar_total_quizzes(self, usuario_id: UUID) -> int:
        try:
            with self.conn.cursor() as cursor:
                query = "SELECT COUNT(*) as total FROM quizzes WHERE usuario_id = %s;"
                cursor.execute(query, (usuario_id,))
                result = cursor.fetchone()
                return result['total'] if result else 0
        except Exception as e:
            raise DashboardDatabaseError("Erro no banco de dados ao contar o total de quizzes.") from e
