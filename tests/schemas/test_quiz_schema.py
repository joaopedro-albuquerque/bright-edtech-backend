from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.quiz_schema import (
    QuestaoConteudoItem,
    QuizConteudoResponse,
    QuizCreateRequest,
    QuizRenomearRequest,
    QuizResponse,
)


class TestQuizCreateRequest:
    def test_usa_valores_default_quando_nao_informados(self):
        request = QuizCreateRequest()

        assert request.quantidade == 10
        assert request.dificuldade == "medio"

    @pytest.mark.parametrize("quantidade", [1, 25, 50])
    def test_aceita_quantidade_dentro_do_limite(self, quantidade):
        request = QuizCreateRequest(quantidade=quantidade)

        assert request.quantidade == quantidade

    @pytest.mark.parametrize("quantidade", [0, 51])
    def test_rejeita_quantidade_fora_do_limite(self, quantidade):
        with pytest.raises(ValidationError):
            QuizCreateRequest(quantidade=quantidade)

    def test_rejeita_dificuldade_fora_do_padrao_permitido(self):
        with pytest.raises(ValidationError):
            QuizCreateRequest(dificuldade="impossivel")


class TestQuizRenomearRequest:
    def test_aceita_titulo_valido(self):
        request = QuizRenomearRequest(titulo="Novo título")

        assert request.titulo == "Novo título"

    def test_rejeita_titulo_vazio(self):
        with pytest.raises(ValidationError):
            QuizRenomearRequest(titulo="")

    def test_rejeita_titulo_acima_do_limite_de_caracteres(self):
        with pytest.raises(ValidationError):
            QuizRenomearRequest(titulo="a" * 256)


def test_quiz_response_constroi_a_partir_de_dados_validos():
    resultado = QuizResponse(
        id=uuid4(), documento_id=uuid4(), titulo="Q", s3_chave="chave",
        tokens_utilizados=10, modelo_ia="modelo-x", criado_em=datetime.utcnow(),
    )

    assert resultado.titulo == "Q"


def test_quiz_conteudo_response_constroi_com_questoes_aninhadas():
    questao = QuestaoConteudoItem(
        id=uuid4(), item_ref="q_001", fator_facilidade=2.5, intervalo_atual=1,
        repeticoes=0, proxima_revisao=datetime.utcnow(), conteudo={"pergunta": "P?"},
    )

    resultado = QuizConteudoResponse(id=uuid4(), titulo="Q", questoes=[questao])

    assert resultado.questoes[0].conteudo["pergunta"] == "P?"
