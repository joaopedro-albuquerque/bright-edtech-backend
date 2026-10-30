from datetime import datetime
from uuid import UUID

from app.core.exceptions import RevisaoDatabaseError

TABELAS_PERMITIDAS = {
    "cartoes": {"origem_fk": "flashcard_id", "tabela_origem": "flashcards"},
    "questoes": {"origem_fk": "quiz_id", "tabela_origem": "quizzes"},
}


def _validar_tabela(tabela: str) -> None:
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError(f"Tabela de revisão inválida: {tabela}")


class RevisaoRepository:
    def __init__(self, conn):
        self.conn = conn

    def buscar_pendentes_hoje(self, usuario_id: UUID, tabela: str, limit: int = 50) -> list:
        _validar_tabela(tabela)
        origem_fk = TABELAS_PERMITIDAS[tabela]["origem_fk"]
        tabela_origem = TABELAS_PERMITIDAS[tabela]["tabela_origem"]
        try:
            with self.conn.cursor() as cursor:
                query = f"""
                    SELECT r.id, r.{origem_fk} AS origem_id, r.item_ref, r.fator_facilidade,
                           r.intervalo_atual, r.repeticoes, r.proxima_revisao, o.s3_chave
                    FROM {tabela} r
                    JOIN {tabela_origem} o ON o.id = r.{origem_fk}
                    WHERE r.usuario_id = %s AND r.proxima_revisao <= now()
                    ORDER BY r.proxima_revisao ASC
                    LIMIT %s;
                """
                cursor.execute(query, (usuario_id, limit))
                return cursor.fetchall()
        except Exception as e:
            raise RevisaoDatabaseError(f"Erro no banco de dados ao buscar pendentes em '{tabela}'.") from e

    def buscar_todos(self, usuario_id: UUID, tabela: str, limit: int = 500) -> list:
        """Mesma consulta de buscar_pendentes_hoje, sem o filtro de data — usada
        pra listar TODOS os itens do usuário (atrasados + em dia), não só os vencidos."""
        _validar_tabela(tabela)
        origem_fk = TABELAS_PERMITIDAS[tabela]["origem_fk"]
        tabela_origem = TABELAS_PERMITIDAS[tabela]["tabela_origem"]
        try:
            with self.conn.cursor() as cursor:
                query = f"""
                    SELECT r.id, r.{origem_fk} AS origem_id, r.item_ref, r.fator_facilidade,
                           r.intervalo_atual, r.repeticoes, r.proxima_revisao, o.s3_chave
                    FROM {tabela} r
                    JOIN {tabela_origem} o ON o.id = r.{origem_fk}
                    WHERE r.usuario_id = %s
                    ORDER BY r.proxima_revisao ASC
                    LIMIT %s;
                """
                cursor.execute(query, (usuario_id, limit))
                return cursor.fetchall()
        except Exception as e:
            raise RevisaoDatabaseError(f"Erro no banco de dados ao buscar todos os itens em '{tabela}'.") from e

    def listar_lotes(self, usuario_id: UUID, tabela: str, limit: int = 500) -> list:
        """Um lote por flashcard/quiz, com documento, caminho da pasta e contagem de
        cartões (total e vencidos). Os lotes com cartões vencidos vêm primeiro."""
        _validar_tabela(tabela)
        origem_fk = TABELAS_PERMITIDAS[tabela]["origem_fk"]
        tabela_origem = TABELAS_PERMITIDAS[tabela]["tabela_origem"]
        try:
            with self.conn.cursor() as cursor:
                query = f"""
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
                    SELECT o.id, o.titulo, o.criado_em, o.documento_id,
                           d.nome AS documento_nome, a.caminho AS pasta_caminho,
                           COUNT(r.id) AS total_itens,
                           COUNT(r.id) FILTER (WHERE r.proxima_revisao <= now()) AS itens_vencidos,
                           MIN(r.proxima_revisao) AS proxima_revisao
                    FROM {tabela_origem} o
                    LEFT JOIN documentos d ON d.id = o.documento_id
                    LEFT JOIN arvore a ON a.id = d.pasta_id
                    LEFT JOIN {tabela} r ON r.{origem_fk} = o.id
                    WHERE o.usuario_id = %s
                    GROUP BY o.id, d.nome, a.caminho
                    ORDER BY itens_vencidos DESC, o.criado_em DESC
                    LIMIT %s;
                """
                cursor.execute(query, (usuario_id, usuario_id, limit))
                return cursor.fetchall()
        except Exception as e:
            raise RevisaoDatabaseError(f"Erro no banco de dados ao listar lotes de '{tabela_origem}'.") from e

    def buscar_por_id(self, item_id: UUID, usuario_id: UUID, tabela: str) -> dict | None:
        _validar_tabela(tabela)
        try:
            with self.conn.cursor() as cursor:
                query = f"""
                    SELECT id, fator_facilidade, intervalo_atual, repeticoes, proxima_revisao
                    FROM {tabela}
                    WHERE id = %s AND usuario_id = %s;
                """
                cursor.execute(query, (item_id, usuario_id))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            raise RevisaoDatabaseError(f"Erro no banco de dados ao buscar item em '{tabela}'.") from e

    def atualizar_estado(
        self,
        item_id: UUID,
        usuario_id: UUID,
        tabela: str,
        fator_facilidade: float,
        intervalo_atual: int,
        repeticoes: int,
        proxima_revisao: datetime,
    ) -> dict | None:
        _validar_tabela(tabela)
        try:
            with self.conn.cursor() as cursor:
                query = f"""
                    UPDATE {tabela}
                    SET fator_facilidade = %s,
                        intervalo_atual = %s,
                        repeticoes = %s,
                        proxima_revisao = %s
                    WHERE id = %s AND usuario_id = %s
                    RETURNING id, fator_facilidade, intervalo_atual, repeticoes, proxima_revisao;
                """
                cursor.execute(query, (
                    fator_facilidade, intervalo_atual, repeticoes, proxima_revisao,
                    item_id, usuario_id,
                ))
                row = cursor.fetchone()

                if not row:
                    self.conn.rollback()
                    return None

                self.conn.commit()
                return dict(row)
        except Exception as e:
            self.conn.rollback()
            raise RevisaoDatabaseError(f"Erro no banco de dados ao atualizar estado em '{tabela}'.") from e
