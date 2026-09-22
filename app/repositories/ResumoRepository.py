from uuid import UUID


class ResumoRepository:
    def __init__(self, conn):
        self.conn = conn

    def criar(
        self,
        documento_id: UUID,
        usuario_id: UUID,
        titulo: str,
        formato: str,
        nivel_conhecimento: int,
        tom: str,
        s3_chave: str,
        tokens_utilizados: int,
        modelo_ia: str,
        s3_chave_pdf: str | None = None,
    ) -> dict:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    INSERT INTO resumos
                        (documento_id, usuario_id, titulo, formato, nivel_conhecimento,
                         tom, s3_chave, s3_chave_pdf, tokens_utilizados, modelo_ia)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, documento_id, titulo, formato, nivel_conhecimento,
                              tom, s3_chave, s3_chave_pdf, tokens_utilizados, modelo_ia, criado_em;
                """
                cursor.execute(query, (
                    documento_id, usuario_id, titulo, formato, nivel_conhecimento,
                    tom, s3_chave, s3_chave_pdf, tokens_utilizados, modelo_ia,
                ))
                row = cursor.fetchone()

                if not row:
                    raise RuntimeError("INSERT executado, mas RETURNING não devolveu o resumo.")

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao criar resumo: {e}")

    def listar_por_documento(self, documento_id: UUID, usuario_id: UUID) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, documento_id, titulo, formato, nivel_conhecimento,
                           tom, s3_chave, s3_chave_pdf, tokens_utilizados, modelo_ia, criado_em
                    FROM resumos
                    WHERE documento_id = %s AND usuario_id = %s
                    ORDER BY criado_em DESC;
                """
                cursor.execute(query, (documento_id, usuario_id))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao listar resumos do documento: {e}")

    def buscar_por_id(self, resumo_id: UUID, usuario_id: UUID) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, documento_id, titulo, formato, nivel_conhecimento,
                           tom, s3_chave, s3_chave_pdf, tokens_utilizados, modelo_ia, criado_em
                    FROM resumos
                    WHERE id = %s AND usuario_id = %s;
                """
                cursor.execute(query, (resumo_id, usuario_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao buscar resumo: {e}")

    def atualizar_titulo(self, resumo_id: UUID, usuario_id: UUID, titulo: str) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    UPDATE resumos SET titulo = %s, atualizado_em = now()
                    WHERE id = %s AND usuario_id = %s
                    RETURNING id, documento_id, titulo, formato, nivel_conhecimento,
                              tom, s3_chave, s3_chave_pdf, tokens_utilizados, modelo_ia, criado_em;
                """
                cursor.execute(query, (titulo, resumo_id, usuario_id))
                row = cursor.fetchone()
                if not row:
                    self.conn.rollback()
                    return None
                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao renomear resumo: {e}")

    def atualizar_s3_chave_pdf(self, resumo_id: UUID, usuario_id: UUID, s3_chave_pdf: str) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    UPDATE resumos SET s3_chave_pdf = %s, atualizado_em = now()
                    WHERE id = %s AND usuario_id = %s
                    RETURNING id, documento_id, titulo, formato, nivel_conhecimento,
                              tom, s3_chave, s3_chave_pdf, tokens_utilizados, modelo_ia, criado_em;
                """
                cursor.execute(query, (s3_chave_pdf, resumo_id, usuario_id))
                row = cursor.fetchone()
                if not row:
                    self.conn.rollback()
                    return None
                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao atualizar chave do PDF do resumo: {e}")

    def deletar(self, resumo_id: UUID, usuario_id: UUID) -> bool:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM resumos WHERE id = %s AND usuario_id = %s;",
                    (resumo_id, usuario_id),
                )
                deleted = cursor.rowcount > 0
                self.conn.commit()
                return deleted
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao deletar resumo: {e}")
