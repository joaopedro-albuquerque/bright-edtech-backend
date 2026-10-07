from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.flashcard_schema import (
    CartaoConteudoItem,
    FlashcardConteudoResponse,
    FlashcardCreateRequest,
    FlashcardRenomearRequest,
    FlashcardResponse,
)


class TestFlashcardCreateRequest:
    def test_usa_valores_default_quando_nao_informados(self):
        request = FlashcardCreateRequest()

        assert request.quantidade == 10
        assert request.dificuldade == "medio"

    @pytest.mark.parametrize("quantidade", [1, 25, 50])
    def test_aceita_quantidade_dentro_do_limite(self, quantidade):
        request = FlashcardCreateRequest(quantidade=quantidade)

        assert request.quantidade == quantidade

    @pytest.mark.parametrize("quantidade", [0, 51, -1])
    def test_rejeita_quantidade_fora_do_limite(self, quantidade):
        with pytest.raises(ValidationError):
            FlashcardCreateRequest(quantidade=quantidade)

    @pytest.mark.parametrize("dificuldade", ["facil", "medio", "dificil"])
    def test_aceita_dificuldades_validas(self, dificuldade):
        request = FlashcardCreateRequest(dificuldade=dificuldade)

        assert request.dificuldade == dificuldade

    def test_rejeita_dificuldade_fora_do_padrao_permitido(self):
        with pytest.raises(ValidationError):
            FlashcardCreateRequest(dificuldade="impossivel")


class TestFlashcardRenomearRequest:
    def test_aceita_titulo_valido(self):
        request = FlashcardRenomearRequest(titulo="Novo título")

        assert request.titulo == "Novo título"

    def test_rejeita_titulo_vazio(self):
        with pytest.raises(ValidationError):
            FlashcardRenomearRequest(titulo="")

    def test_rejeita_titulo_acima_do_limite_de_caracteres(self):
        with pytest.raises(ValidationError):
            FlashcardRenomearRequest(titulo="a" * 256)


def test_flashcard_response_constroi_a_partir_de_dados_validos():
    resultado = FlashcardResponse(
        id=uuid4(), documento_id=uuid4(), titulo="F", s3_chave="chave",
        tokens_utilizados=10, modelo_ia="modelo-x", criado_em=datetime.utcnow(),
    )

    assert resultado.titulo == "F"


def test_flashcard_conteudo_response_constroi_com_cartoes_aninhados():
    cartao = CartaoConteudoItem(
        id=uuid4(), item_ref="card_001", fator_facilidade=2.5, intervalo_atual=1,
        repeticoes=0, proxima_revisao=datetime.utcnow(), conteudo={"pergunta": "P?"},
    )

    resultado = FlashcardConteudoResponse(id=uuid4(), titulo="F", cartoes=[cartao])

    assert resultado.cartoes[0].conteudo["pergunta"] == "P?"
