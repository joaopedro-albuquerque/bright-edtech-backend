from uuid import UUID, uuid4
from app.schemas.user_schema import Pasta, PastaBase
# import logging
# logger = logging.getLogger(__name__)

class DocumentRepository:
    def __init__(self, conn):
        self.conn = conn

    def criar_pasta(self, pasta: PastaBase) -> dict:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    INSERT INTO pastas (usuario_id, nome, pasta_pai_id)
                    VALUES (%s, %s, %s)
                    RETURNING id, usuario_id, nome, pasta_pai_id, criada_em;
                """
                cursor.execute(query, (pasta.usuario_id, pasta.nome, pasta.pasta_pai_id))
                row = cursor.fetchone()
                self.conn.commit()
                
                if not row:
                    raise RuntimeError("A query executou, mas o RETURNING não devolveu os dados.")
                    
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao criar pasta: {e}")

    def criar_documento(
        self,
        usuario_id: UUID,
        pasta_id: UUID,
        nome: str,
        file_ext: str,
        nivel_conhecimento: str = "iniciante"
    ) -> dict:
        placeholder = f"tmp-{uuid4()}"

        try:
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
                    raise RuntimeError("INSERT executado, mas RETURNING falhou.")

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao criar documento: {e}")

    def atualizar_chave_s3(self, documento_id: UUID, chave_s3: str) -> dict:
        try:
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
                    raise RuntimeError(f"Nenhum documento encontrado para atualizar com id {documento_id}.")

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao atualizar chave S3: {e}")

    def buscar_chave_s3_por_documento_id_e_usuario(self, documento_id: UUID, usuario_id: UUID) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT chave_s3
                    FROM documentos
                    WHERE id = %s AND usuario_id = %s
                    LIMIT 1;
                """
                cursor.execute(query, (documento_id, usuario_id))
                return cursor.fetchone()
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao buscar chave S3: {e}")
        
    def listar_pastas_raiz_por_usuario(self, usuario_id: UUID, limit: int, offset: int) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT * FROM pastas 
                    WHERE usuario_id = %s AND pasta_pai_id IS NULL
                    ORDER BY criada_em DESC
                    LIMIT %s OFFSET %s;
                """
                cursor.execute(query, (usuario_id, limit, offset))
                return cursor.fetchall()
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao listar pastas raiz: {e}")

    def listar_todas_pastas_por_usuario(self, usuario_id: UUID) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, nome, criada_em
                    FROM pastas
                    WHERE usuario_id = %s
                    ORDER BY criada_em DESC;
                """
                cursor.execute(query, (usuario_id,))
                return cursor.fetchall()
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao listar todas as pastas: {e}")
    
    def listar_conteudo_pasta(self, pasta_id: UUID, limit: int, offset: int) -> dict:
        try:
            with self.conn.cursor() as cursor:
                # 1. Buscar subpastas imediatas
                query_subpastas = """
                    SELECT id, nome, criada_em 
                    FROM pastas 
                    WHERE pasta_pai_id = %s 
                    ORDER BY nome ASC;
                """
                cursor.execute(query_subpastas, (pasta_id,))
                subpastas = cursor.fetchall()

                # 2. Buscar documentos com paginação
                query_documentos = """
                SELECT id, nome, status, resumo  
                FROM documentos 
                WHERE pasta_id = %s 
                ORDER BY criado_em DESC 
                LIMIT %s OFFSET %s;
                """
                cursor.execute(query_documentos, (pasta_id, limit, offset))
                arquivos = cursor.fetchall()

                # 3. Contar total de documentos
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
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao listar conteúdo da pasta: {e}")

    def atualizar_pasta_nome(self, pasta_id: UUID, nome: str) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE pastas SET nome = %s WHERE id = %s RETURNING id, usuario_id, pasta_pai_id, nome, criada_em;",
                    (nome, pasta_id)
                )
                row = cursor.fetchone()
                
                if not row:
                    self.conn.rollback()
                    return None
                    
                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao atualizar nome da pasta: {e}")

    def deletar_pasta(self, pasta_id: UUID) -> bool:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM pastas WHERE id = %s;",
                    (pasta_id,)
                )
                deleted = cursor.rowcount > 0
                self.conn.commit()
                return deleted
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao deletar pasta: {e}")
    
    def inserir_documento(
        self, usuario_id: UUID, pasta_id: UUID, nome: str, chave_s3: str, resumo: str
    ) -> dict:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    INSERT INTO documentos (usuario_id, pasta_id, nome, chave_s3, nivel_conhecimento, status, resumo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, nome, status, criado_em;
                """
                valores = (usuario_id, pasta_id, nome, chave_s3, 'basico', 'concluido', resumo)
                cursor.execute(query, valores)
                
                row = cursor.fetchone()
                if not row:
                    raise RuntimeError("Falha ao retornar os dados inseridos (RETURNING vazio).")
                    
                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao inserir documento processado: {e}")
        
    def inserir_resumo_registro_documento(
        self, usuario_id: UUID, id_documento: UUID, resumo: str
         ) -> dict:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    UPDATE documentos
                    SET resumo = %s, status = 'pronto'
                    WHERE id = %s AND usuario_id = %s
                    RETURNING resumo;
                """
                valores = (resumo, id_documento, usuario_id)
                cursor.execute(query, valores)
                
                row = cursor.fetchone()
                if not row:
                    raise RuntimeError("Falha ao retornar os dados inseridos (RETURNING vazio).")
                    
                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao inserir resumo: {e}")

    def buscar_resumo_por_id(self, documento_id: UUID, usuario_id: UUID) -> dict | None:
            try:
                with self.conn.cursor() as cursor:
                    query = """
                        SELECT resumo
                        FROM documentos
                        WHERE id = %s AND usuario_id = %s
                        LIMIT 1;
                    """
                    cursor.execute(query, (documento_id, usuario_id))
                    row = cursor.fetchone()
                    
                    return dict(row) if row else None
                    
            except Exception as e:
                raise RuntimeError(f"Erro no banco de dados ao buscar resumo: {e}")