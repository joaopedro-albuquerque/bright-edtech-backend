from uuid import UUID

import psycopg2.extras


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
                    raise RuntimeError("INSERT de quiz não retornou dados.")

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
            raise RuntimeError(f"Erro no banco de dados ao criar quiz: {e}")

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
            raise RuntimeError(f"Erro no banco de dados ao deletar quiz: {e}")
