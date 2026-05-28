from uuid import UUID

class DashboardRepository:
    def __init__(self, conn):
        self.conn = conn

    def buscar_ultimos_flashcards(self, usuario_id: UUID, limit: int = 5) -> list:
        with self.conn.cursor() as cursor:
            query = """
                SELECT id, titulo, criado_em
                FROM flashcards
                WHERE usuario_id = %s
                ORDER BY criado_em DESC
                LIMIT %s;
            """
            cursor.execute(query, (usuario_id, limit))
            rows = cursor.fetchall()
            return rows

    def buscar_ultimos_resumos(self, usuario_id: UUID, limit: int = 5) -> list:
        with self.conn.cursor() as cursor:
            query = """
                SELECT id, nome, criado_em
                FROM documentos
                WHERE usuario_id = %s AND resumo IS NOT NULL
                ORDER BY criado_em DESC
                LIMIT %s;
            """
            cursor.execute(query, (usuario_id, limit))
            rows = cursor.fetchall()
            return rows

    def buscar_ultimos_quizzes(self, usuario_id: UUID, limit: int = 5) -> list:
        with self.conn.cursor() as cursor:
            query = """
                SELECT id, titulo, criado_em
                FROM quizzes
                WHERE usuario_id = %s
                ORDER BY criado_em DESC
                LIMIT %s;
            """
            cursor.execute(query, (usuario_id, limit))
            rows = cursor.fetchall()
            return rows

    def contar_total_flashcards(self, usuario_id: UUID) -> int:
        with self.conn.cursor() as cursor:
            query = "SELECT COUNT(*) as total FROM flashcards WHERE usuario_id = %s;"
            cursor.execute(query, (usuario_id,))
            result = cursor.fetchone()
            return result['total'] if result else 0

    def contar_total_resumos(self, usuario_id: UUID) -> int:
        with self.conn.cursor() as cursor:
            query = "SELECT COUNT(*) as total FROM documentos WHERE usuario_id = %s AND resumo IS NOT NULL;"
            cursor.execute(query, (usuario_id,))
            result = cursor.fetchone()
            return result['total'] if result else 0

    def contar_total_quizzes(self, usuario_id: UUID) -> int:
        with self.conn.cursor() as cursor:
            query = "SELECT COUNT(*) as total FROM quizzes WHERE usuario_id = %s;"
            cursor.execute(query, (usuario_id,))
            result = cursor.fetchone()
            return result['total'] if result else 0
