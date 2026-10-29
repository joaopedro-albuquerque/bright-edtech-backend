from uuid import UUID, uuid4

from app.core.exceptions import DocumentDatabaseError

_COM_ACENTO = "áàâãäéèêëíìîïóòôõöúùûüç"
_SEM_ACENTO = "aaaaaeeeeiiiiooooouuuuc"
_TRADUCAO_ACENTOS = str.maketrans(_COM_ACENTO, _SEM_ACENTO)
_CARACTER_ESCAPE = "!"


def montar_padrao_busca(termo: str) -> str:
    """Termo -> padrão LIKE sem acento/caixa, com %, _ e o próprio escape neutralizados."""
    normalizado = termo.strip().lower().translate(_TRADUCAO_ACENTOS)
    for especial in (_CARACTER_ESCAPE, "%", "_"):
        normalizado = normalizado.replace(especial, _CARACTER_ESCAPE + especial)
    return f"%{normalizado}%"


class DocumentRepository:
    def __init__(self, conn):
        self.conn = conn

    def criar_pasta(self, usuario_id: UUID, nome: str, pasta_pai_id: UUID | None) -> dict:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    INSERT INTO pastas (usuario_id, nome, pasta_pai_id)
                    VALUES (%s, %s, %s)
                    RETURNING id, usuario_id, nome, pasta_pai_id, criada_em;
                """
                cursor.execute(query, (usuario_id, nome, pasta_pai_id))
                row = cursor.fetchone()
                self.conn.commit()

                if not row:
                    raise DocumentDatabaseError("A query executou, mas o RETURNING não devolveu os dados.")

                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise DocumentDatabaseError("Erro no banco de dados ao criar pasta.") from e

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
                    raise DocumentDatabaseError("INSERT executado, mas RETURNING falhou.")

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise DocumentDatabaseError("Erro no banco de dados ao criar documento.") from e

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
                    raise DocumentDatabaseError(f"Nenhum documento encontrado para atualizar com id {documento_id}.")

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise DocumentDatabaseError("Erro no banco de dados ao atualizar chave S3.") from e

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
            raise DocumentDatabaseError("Erro no banco de dados ao buscar chave S3.") from e

    def buscar_documentos(self, usuario_id: UUID, termo: str, limit: int, offset: int) -> dict:
        try:
            with self.conn.cursor() as cursor:
                condicao = f"""
                    d.usuario_id = %s
                    AND translate(lower(d.nome), '{_COM_ACENTO}', '{_SEM_ACENTO}')
                        LIKE %s ESCAPE '{_CARACTER_ESCAPE}'
                """
                padrao = montar_padrao_busca(termo)

                # A árvore monta o caminho completo de cada pasta (ex.: "Faculdade › Semestre 6").
                cursor.execute(
                    f"""
                    WITH RECURSIVE arvore AS (
                        SELECT id, nome::text AS caminho, 1 AS nivel
                        FROM pastas
                        WHERE usuario_id = %s AND pasta_pai_id IS NULL
                        UNION ALL
                        SELECT p.id, a.caminho || ' › ' || p.nome, a.nivel + 1
                        FROM pastas p
                        JOIN arvore a ON p.pasta_pai_id = a.id
                        WHERE a.nivel < 20
                    )
                    SELECT d.id, d.nome, p.nome AS pasta_nome, a.caminho AS pasta_caminho, d.criado_em
                    FROM documentos d
                    LEFT JOIN pastas p ON p.id = d.pasta_id
                    LEFT JOIN arvore a ON a.id = d.pasta_id
                    WHERE {condicao}
                    ORDER BY d.criado_em DESC, d.id
                    LIMIT %s OFFSET %s;
                    """,
                    (usuario_id, usuario_id, padrao, limit, offset),
                )
                itens = cursor.fetchall()

                cursor.execute(
                    f"SELECT count(*) AS total FROM documentos d WHERE {condicao};",
                    (usuario_id, padrao),
                )
                total = cursor.fetchone()["total"]

                return {"itens": itens, "total": total}
        except Exception as e:
            raise DocumentDatabaseError("Erro no banco de dados ao buscar documentos.") from e

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
            raise DocumentDatabaseError("Erro no banco de dados ao listar pastas raiz.") from e

    def listar_todas_pastas_por_usuario(self, usuario_id: UUID) -> list:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, nome, pasta_pai_id, criada_em
                    FROM pastas
                    WHERE usuario_id = %s
                    ORDER BY criada_em DESC;
                """
                cursor.execute(query, (usuario_id,))
                return cursor.fetchall()
        except Exception as e:
            raise DocumentDatabaseError("Erro no banco de dados ao listar todas as pastas.") from e

    def listar_conteudo_pasta(self, pasta_id: UUID, usuario_id: UUID, limit: int, offset: int) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pastas WHERE id = %s AND usuario_id = %s;", (pasta_id, usuario_id))
                if not cursor.fetchone():
                    return None

                query_subpastas = """
                    SELECT id, nome, criada_em
                    FROM pastas
                    WHERE pasta_pai_id = %s
                    ORDER BY nome ASC;
                """
                cursor.execute(query_subpastas, (pasta_id,))
                subpastas = cursor.fetchall()

                query_documentos = """
                SELECT id, nome, status, resumo
                FROM documentos
                WHERE pasta_id = %s
                ORDER BY criado_em DESC
                LIMIT %s OFFSET %s;
                """
                cursor.execute(query_documentos, (pasta_id, limit, offset))
                arquivos = cursor.fetchall()

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
            raise DocumentDatabaseError("Erro no banco de dados ao listar conteúdo da pasta.") from e

    def atualizar_pasta_nome(self, pasta_id: UUID, nome: str, usuario_id: UUID) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE pastas SET nome = %s WHERE id = %s AND usuario_id = %s "
                    "RETURNING id, usuario_id, pasta_pai_id, nome, criada_em;",
                    (nome, pasta_id, usuario_id)
                )
                row = cursor.fetchone()

                if not row:
                    self.conn.rollback()
                    return None

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise DocumentDatabaseError("Erro no banco de dados ao atualizar nome da pasta.") from e

    def deletar_pasta(self, pasta_id: UUID, usuario_id: UUID) -> bool:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM pastas WHERE id = %s AND usuario_id = %s;",
                    (pasta_id, usuario_id)
                )
                deleted = cursor.rowcount > 0
                self.conn.commit()
                return deleted
        except Exception as e:
            self.conn.rollback()
            raise DocumentDatabaseError("Erro no banco de dados ao deletar pasta.") from e

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
                    raise DocumentDatabaseError("Falha ao retornar os dados inseridos (RETURNING vazio).")

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise DocumentDatabaseError("Erro no banco de dados ao inserir documento processado.") from e

    def atualizar_documento_nome(self, documento_id: UUID, nome: str, usuario_id: UUID) -> dict | None:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE documentos SET nome = %s WHERE id = %s AND usuario_id = %s
                    RETURNING id, usuario_id, pasta_id, nome, chave_s3, status, criado_em;
                    """,
                    (nome, documento_id, usuario_id)
                )
                row = cursor.fetchone()

                if not row:
                    self.conn.rollback()
                    return None

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise DocumentDatabaseError("Erro no banco de dados ao atualizar nome do documento.") from e

    def deletar_documento(self, documento_id: UUID, usuario_id: UUID) -> bool:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM documentos WHERE id = %s AND usuario_id = %s;",
                    (documento_id, usuario_id)
                )
                deleted = cursor.rowcount > 0
                self.conn.commit()
                return deleted
        except Exception as e:
            self.conn.rollback()
            raise DocumentDatabaseError("Erro no banco de dados ao deletar documento.") from e
