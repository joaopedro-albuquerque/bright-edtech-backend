from uuid import UUID

import psycopg2.extras


class FlashcardRepository:
    def __init__(self, conn):
        self.conn = conn

    def criar_flashcard_com_cartoes(
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
                query_flashcard = """
                    INSERT INTO flashcards
                        (usuario_id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia, criado_em;
                """
                cursor.execute(query_flashcard, (
                    usuario_id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia,
                ))
                flashcard_row = cursor.fetchone()

                if not flashcard_row:
                    raise RuntimeError("INSERT de flashcard não retornou dados.")

                flashcard_id = flashcard_row["id"]

                query_cartao = """
                    INSERT INTO cartoes (flashcard_id, usuario_id, item_ref)
                    VALUES %s;
                """
                valores = [(flashcard_id, usuario_id, item_ref) for item_ref in item_refs]
                psycopg2.extras.execute_values(cursor, query_cartao, valores)

                self.conn.commit()
                return dict(flashcard_row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao criar flashcard: {e}")

    def listar_por_documento(self, documento_id: UUID, usuario_id: UUID) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia, criado_em
                    FROM flashcards
                    WHERE documento_id = %s AND usuario_id = %s
                    ORDER BY criado_em DESC;
                """
                cursor.execute(query, (documento_id, usuario_id))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao listar flashcards do documento: {e}")

    def buscar_por_id(self, flashcard_id: UUID, usuario_id: UUID) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, documento_id, titulo, s3_chave, tokens_utilizados, modelo_ia, criado_em
                    FROM flashcards
                    WHERE id = %s AND usuario_id = %s;
                """
                cursor.execute(query, (flashcard_id, usuario_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao buscar flashcard: {e}")

    def listar_cartoes_por_flashcard(self, flashcard_id: UUID, usuario_id: UUID) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, flashcard_id, item_ref, fator_facilidade, intervalo_atual,
                           repeticoes, proxima_revisao
                    FROM cartoes
                    WHERE flashcard_id = %s AND usuario_id = %s
                    ORDER BY item_ref ASC;
                """
                cursor.execute(query, (flashcard_id, usuario_id))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao listar cartões do flashcard: {e}")

    def deletar(self, flashcard_id: UUID, usuario_id: UUID) -> bool:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM flashcards WHERE id = %s AND usuario_id = %s;",
                    (flashcard_id, usuario_id),
                )
                deleted = cursor.rowcount > 0
                self.conn.commit()
                return deleted
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao deletar flashcard: {e}")
