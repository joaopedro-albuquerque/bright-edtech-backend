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
        
    def listar_pastas_raiz_por_usuario(self, usuario_id: UUID, limit: int, offset: int) -> list:
        with self.conn.cursor() as cursor:
            query = """
                SELECT * FROM pastas 
                WHERE usuario_id = %s AND parent_id IS NULL
                ORDER BY criada_em DESC
                LIMIT %s OFFSET %s;
            """
            
            cursor.execute(query, (usuario_id, limit, offset))
            rows = cursor.fetchall()

            return rows
    
    def listar_conteudo_pasta(self, pasta_id: UUID, limit: int, offset: int) -> dict:
        with self.conn.cursor() as cursor:
            # 1. Buscar subpastas imediatas (sem paginação, volume previsível)
            query_subpastas = """
                SELECT id, nome, criada_em 
                FROM pastas 
                WHERE parent_id = %s 
                ORDER BY nome ASC;
            """
            cursor.execute(query_subpastas, (pasta_id,))
            subpastas = cursor.fetchall()

            # 2. Buscar documentos com paginação
            query_documentos = """
                SELECT id, nome, status 
                FROM documentos 
                WHERE pasta_id = %s 
                ORDER BY criado_em DESC 
                LIMIT %s OFFSET %s;
            """
            cursor.execute(query_documentos, (pasta_id, limit, offset))
            arquivos = cursor.fetchall()

            # 3. Contar total de documentos para metadados de paginação
            query_count = """
                SELECT count(*) as total 
                FROM documentos 
                WHERE pasta_id = %s;
            """
            cursor.execute(query_count, (pasta_id,))
            total_arquivos = cursor.fetchone()['total']

            return {
                "subpastas": subpastas,
                "arquivos": arquivos,
                "total_arquivos": total_arquivos,
                "pagina_atual": (offset // limit) + 1,
                "tem_mais_paginas": (offset + limit) < total_arquivos
            }

    def atualizar_pasta_nome(self, pasta_id: UUID, nome: str) -> dict | None:
        with self.conn.cursor() as cursor:
            cursor.execute(
                "UPDATE pastas SET nome = %s WHERE id = %s RETURNING id, usuario_id, pasta_pai_id AS parent_id, nome, criada_em;",
                (nome, pasta_id)
            )
            row = cursor.fetchone()
            if not row:
                self.conn.rollback()
                return None
            self.conn.commit()
            return dict(row)

    def deletar_pasta(self, pasta_id: UUID) -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM pastas WHERE id = %s;",
                (pasta_id,)
            )
            deleted = cursor.rowcount > 0
            self.conn.commit()
            return deleted