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
