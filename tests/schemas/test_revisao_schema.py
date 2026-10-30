from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.revisao_schema import (
    AvaliarRequest,
    AvaliarResponse,
    DailyMixResponse,
    ItemRevisaoResponse,
    LoteRevisaoResponse,
)


class TestAvaliarRequest:
    @pytest.mark.parametrize("qualidade", [1, 3, 5])
    def test_aceita_qualidade_dentro_do_limite(self, qualidade):
        request = AvaliarRequest(qualidade=qualidade)

        assert request.qualidade == qualidade

    @pytest.mark.parametrize("qualidade", [0, 6, -1])
    def test_rejeita_qualidade_fora_do_limite(self, qualidade):
        with pytest.raises(ValidationError):
            AvaliarRequest(qualidade=qualidade)


def _item_revisao():
    return ItemRevisaoResponse(
        id=uuid4(), origem_id=uuid4(), item_ref="card_001", fator_facilidade=2.5,
        intervalo_atual=1, repeticoes=0, proxima_revisao=datetime.utcnow(), conteudo=None,
    )


def test_daily_mix_response_agrega_cartoes_e_questoes():
    resultado = DailyMixResponse(cartoes=[_item_revisao()], questoes=[_item_revisao()], total=2)

    assert resultado.total == 2
    assert len(resultado.cartoes) == 1
    assert len(resultado.questoes) == 1


def test_avaliar_response_constroi_a_partir_de_dados_validos():
    resultado = AvaliarResponse(
        id=uuid4(), fator_facilidade=2.6, intervalo_atual=6, repeticoes=1, proxima_revisao=datetime.utcnow(),
    )

    assert resultado.fator_facilidade == 2.6


class TestLoteRevisaoResponse:
    def test_aceita_lote_sem_documento(self):
        lote = LoteRevisaoResponse(
            id=uuid4(), titulo="Flashcards Gerados", criado_em=datetime.now(),
            total_itens=12, itens_vencidos=4,
        )

        assert lote.documento_id is None
        assert lote.proxima_revisao is None

    def test_aceita_lote_com_documento_e_pasta(self):
        lote = LoteRevisaoResponse(
            id=uuid4(), titulo="Flashcards Gerados", criado_em=datetime.now(),
            documento_id=uuid4(), documento_nome="Aula 3 - Ética.pdf",
            pasta_caminho="Faculdade › Semestre 1", total_itens=12, itens_vencidos=4,
            proxima_revisao=datetime.now(),
        )

        assert lote.pasta_caminho == "Faculdade › Semestre 1"
