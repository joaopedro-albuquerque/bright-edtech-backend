import logging
from uuid import UUID

from app.repositories.RevisaoRepository import RevisaoRepository
from app.services.S3Service import S3Service
from app.services.SpacedRepetitionService import SpacedRepetitionService

logger = logging.getLogger(__name__)


class RevisaoService:
    def __init__(
        self,
        revisao_repo: RevisaoRepository,
        s3_service: S3Service | None = None,
        spaced_repetition: SpacedRepetitionService | None = None,
    ):
        self.revisao_repo = revisao_repo
        self.s3_service = s3_service or S3Service()
        self.spaced_repetition = spaced_repetition or SpacedRepetitionService()

    def buscar_daily_mix(self, usuario_id: UUID) -> dict:
        cartoes = self._buscar_e_enriquecer(usuario_id, "cartoes")
        questoes = self._buscar_e_enriquecer(usuario_id, "questoes")

        return {
            "cartoes": cartoes,
            "questoes": questoes,
            "total": len(cartoes) + len(questoes),
        }

    def buscar_flashcards_pendentes(self, usuario_id: UUID) -> list:
        return self._buscar_e_enriquecer(usuario_id, "cartoes")

    def buscar_quizzes_pendentes(self, usuario_id: UUID) -> list:
        return self._buscar_e_enriquecer(usuario_id, "questoes")

    def avaliar_cartao(self, cartao_id: UUID, usuario_id: UUID, qualidade: int) -> dict:
        return self._avaliar(cartao_id, usuario_id, qualidade, "cartoes")

    def avaliar_questao(self, questao_id: UUID, usuario_id: UUID, qualidade: int) -> dict:
        return self._avaliar(questao_id, usuario_id, qualidade, "questoes")

    # Helpers
    def _buscar_e_enriquecer(self, usuario_id: UUID, tabela: str) -> list:
        pendentes = self.revisao_repo.buscar_pendentes_hoje(usuario_id, tabela)
        conteudo_cache: dict[str, list] = {}
        resultado = []

        for item in pendentes:
            s3_chave = item["s3_chave"]

            if s3_chave not in conteudo_cache:
                try:
                    conteudo_cache[s3_chave] = self.s3_service.download_json(s3_chave)
                except Exception:
                    logger.warning(f"Falha ao baixar conteúdo do S3: {s3_chave}", exc_info=True)
                    conteudo_cache[s3_chave] = []

            itens_json = conteudo_cache[s3_chave]
            conteudo_item = next((i for i in itens_json if i.get("item_ref") == item["item_ref"]), None)

            resultado.append({
                "id": item["id"],
                "origem_id": item["origem_id"],
                "item_ref": item["item_ref"],
                "fator_facilidade": item["fator_facilidade"],
                "intervalo_atual": item["intervalo_atual"],
                "repeticoes": item["repeticoes"],
                "proxima_revisao": item["proxima_revisao"],
                "conteudo": conteudo_item,
            })

        return resultado

    def _avaliar(self, item_id: UUID, usuario_id: UUID, qualidade: int, tabela: str) -> dict:
        item_atual = self.revisao_repo.buscar_por_id(item_id, usuario_id, tabela)
        if not item_atual:
            raise ValueError("Item de revisão não encontrado.")

        novo_estado = self.spaced_repetition.avaliar(
            fator_facilidade=item_atual["fator_facilidade"],
            intervalo_atual=item_atual["intervalo_atual"],
            repeticoes=item_atual["repeticoes"],
            qualidade=qualidade,
        )

        resultado = self.revisao_repo.atualizar_estado(
            item_id=item_id,
            usuario_id=usuario_id,
            tabela=tabela,
            fator_facilidade=novo_estado["fator_facilidade"],
            intervalo_atual=novo_estado["intervalo_atual"],
            repeticoes=novo_estado["repeticoes"],
            proxima_revisao=novo_estado["proxima_revisao"],
        )

        if not resultado:
            raise ValueError("Item de revisão não encontrado ao atualizar.")

        return resultado
