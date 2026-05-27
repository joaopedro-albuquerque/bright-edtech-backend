from uuid import UUID, uuid4
from app.schemas.user_schema import Pasta, PastaBase

class DocumentRepository:
    def __init__(self, conn):
        self.conn = conn

    def criar_pasta(self, pasta: PastaBase) -> dict:
        with self.conn.cursor() as cursor:
            query = """
                INSERT INTO pastas (user_id, nome, parent_id)
                VALUES (%s, %s, %s)
                RETURNING id, user_id, nome, parent_id, criado_em;
            """
            cursor.execute(query, (pasta.user_id, pasta.nome, pasta.parent_id))
            row = cursor.fetchone()
            self.conn.commit()
            return dict(row)

    def criar_documento(
        self,
        usuario_id: UUID,
        pasta_id: UUID,
        nome: str,
        file_ext: str,
        nivel_conhecimento: str = "iniciante"
    ) -> dict:
        placeholder = f"tmp-{uuid4()}"

        with self.conn.cursor() as cursor:
            insert_query = """
                INSERT INTO documentos
                    (usuario_id, pasta_id, nome, chave_s3, nivel_conhecimento)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, usuario_id, pasta_id, nome, chave_s3,
                          nivel_conhecimento, status, resumo, criado_em;
            """
            cursor.execute(
                insert_query,
                (usuario_id, pasta_id, nome, placeholder, nivel_conhecimento)
            )
            row = cursor.fetchone()
            if not row:
                self.conn.rollback()
                raise RuntimeError("Falha ao inserir documento")

            self.conn.commit()
            return dict(row)

    def atualizar_chave_s3(self, documento_id: UUID, chave_s3: str) -> dict:
        with self.conn.cursor() as cursor:
            update_query = """
                UPDATE documentos
                SET chave_s3 = %s
                WHERE id = %s
                RETURNING id, usuario_id, pasta_id, nome, chave_s3,
                          nivel_conhecimento, status, resumo, criado_em;
            """
            cursor.execute(update_query, (chave_s3, documento_id))
            row = cursor.fetchone()
            if not row:
                self.conn.rollback()
                raise RuntimeError("Falha ao atualizar chave S3 do documento")

            self.conn.commit()
            return dict(row) 