from uuid import UUID

import psycopg2.extras

from app.core.exceptions import QuizDatabaseError


class QuizRepository:
    def __init__(self, conn):
        self.conn = conn

    def criar_quiz_com_questoes(
        self,
        usuario_id: UUID,
        documento_id: UUID | None,
        titulo: str,
        s3_chave: str,
        tokens_utilizados: int,
        modelo_ia: str,
        item_refs: list[str],
    ) -> dict:
        try:
            with self.conn.cursor() as cursor:
                query_quiz = """
                    INSERT INTO quizzes
                        (usuario_id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia, criado_em;
                """
                cursor.execute(query_quiz, (
                    usuario_id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia,
                ))
                quiz_row = cursor.fetchone()

                if not quiz_row:
                    raise QuizDatabaseError("INSERT de quiz não retornou dados.")

                quiz_id = quiz_row["id"]

                query_questao = """
                    INSERT INTO questoes (quiz_id, usuario_id, item_ref)
                    VALUES %s;
                """
                valores = [(quiz_id, usuario_id, item_ref) for item_ref in item_refs]
                psycopg2.extras.execute_values(cursor, query_questao, valores)

                self.conn.commit()
                return dict(quiz_row)
        except Exception as e:
            self.conn.rollback()
            raise QuizDatabaseError("Erro no banco de dados ao criar quiz.") from e

    def listar_por_documento(self, documento_id: UUID, usuario_id: UUID) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia, criado_em
                    FROM quizzes
                    WHERE documento_id = %s AND usuario_id = %s
                    ORDER BY criado_em DESC;
                """
                cursor.execute(query, (documento_id, usuario_id))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise QuizDatabaseError("Erro no banco de dados ao listar quizzes do documento.") from e

    def buscar_por_id(self, quiz_id: UUID, usuario_id: UUID) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia, criado_em
                    FROM quizzes
                    WHERE id = %s AND usuario_id = %s;
                """
                cursor.execute(query, (quiz_id, usuario_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            raise QuizDatabaseError("Erro no banco de dados ao buscar quiz.") from e

    def listar_questoes_por_quiz(self, quiz_id: UUID, usuario_id: UUID, somente_vencidos: bool = False) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, quiz_id, item_ref, fator_facilidade, intervalo_atual,
                           repeticoes, proxima_revisao
                    FROM questoes
                    WHERE quiz_id = %s AND usuario_id = %s
                      AND (NOT %s OR proxima_revisao <= now())
                    ORDER BY item_ref ASC;
                """
                cursor.execute(query, (quiz_id, usuario_id, somente_vencidos))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise QuizDatabaseError("Erro no banco de dados ao listar questões do quiz.") from e

    def atualizar_titulo(self, quiz_id: UUID, usuario_id: UUID, titulo: str) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    UPDATE quizzes SET titulo = %s
                    WHERE id = %s AND usuario_id = %s
                    RETURNING id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia, criado_em;
                """
                cursor.execute(query, (titulo, quiz_id, usuario_id))
                row = cursor.fetchone()
                if not row:
                    self.conn.rollback()
                    return None
                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise QuizDatabaseError("Erro no banco de dados ao renomear quiz.") from e

    def deletar(self, quiz_id: UUID, usuario_id: UUID) -> bool:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM quizzes WHERE id = %s AND usuario_id = %s;",
                    (quiz_id, usuario_id),
                )
                deleted = cursor.rowcount > 0
                self.conn.commit()
                return deleted
        except Exception as e:
            self.conn.rollback()
            raise QuizDatabaseError("Erro no banco de dados ao deletar quiz.") from e
