from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import RevisaoNotFoundError
from app.services.RevisaoService import RevisaoService


@pytest.fixture
def revisao_repo(mocker):
    return mocker.MagicMock()


@pytest.fixture
def s3_service(mocker):
    return mocker.MagicMock()


@pytest.fixture
def spaced_repetition(mocker):
    return mocker.MagicMock()


@pytest.fixture
def service(revisao_repo, s3_service, spaced_repetition):
    return RevisaoService(revisao_repo, s3_service, spaced_repetition)


def _item(item_id=None, s3_chave="chave.json", item_ref="card_001"):
    return {
        "id": item_id or uuid4(),
        "origem_id": uuid4(),
        "item_ref": item_ref,
        "fator_facilidade": 2.5,
        "intervalo_atual": 1,
        "repeticoes": 0,
        "proxima_revisao": datetime.utcnow(),
        "s3_chave": s3_chave,
    }


class TestBuscarDailyMix:
    def test_combina_cartoes_e_questoes_com_total(self, service, revisao_repo, s3_service):
        revisao_repo.buscar_pendentes_hoje.side_effect = [[_item()], [_item(item_ref="q_001")]]
        s3_service.download_json.return_value = [{"item_ref": "card_001"}, {"item_ref": "q_001"}]

        resultado = service.buscar_daily_mix(uuid4())

        assert resultado["total"] == 2
        assert len(resultado["cartoes"]) == 1
        assert len(resultado["questoes"]) == 1


class TestBuscarPendentes:
    def test_buscar_flashcards_pendentes_usa_tabela_cartoes_sem_todos(self, service, revisao_repo, s3_service):
        revisao_repo.buscar_pendentes_hoje.return_value = [_item()]
        s3_service.download_json.return_value = [{"item_ref": "card_001"}]

        resultado = service.buscar_flashcards_pendentes(uuid4())

        assert len(resultado) == 1
        revisao_repo.buscar_pendentes_hoje.assert_called_once()

    def test_buscar_quizzes_pendentes_usa_tabela_questoes(self, service, revisao_repo, s3_service):
        revisao_repo.buscar_pendentes_hoje.return_value = [_item(item_ref="q_001")]
        s3_service.download_json.return_value = [{"item_ref": "q_001"}]

        resultado = service.buscar_quizzes_pendentes(uuid4())

        assert len(resultado) == 1

    def test_buscar_flashcards_todos_usa_buscar_todos_do_repositorio(self, service, revisao_repo, s3_service):
        revisao_repo.buscar_todos.return_value = [_item()]
        s3_service.download_json.return_value = [{"item_ref": "card_001"}]

        resultado = service.buscar_flashcards_todos(uuid4())

        assert len(resultado) == 1
        revisao_repo.buscar_todos.assert_called_once()

    def test_buscar_quizzes_todos_usa_buscar_todos_do_repositorio(self, service, revisao_repo, s3_service):
        revisao_repo.buscar_todos.return_value = [_item(item_ref="q_001")]
        s3_service.download_json.return_value = [{"item_ref": "q_001"}]

        resultado = service.buscar_quizzes_todos(uuid4())

        assert len(resultado) == 1
        revisao_repo.buscar_todos.assert_called_once()


class TestEnriquecimentoComS3:
    def test_falha_no_s3_usa_lista_vazia_como_fallback(self, service, revisao_repo, s3_service):
        revisao_repo.buscar_pendentes_hoje.return_value = [_item()]
        s3_service.download_json.side_effect = Exception("s3 indisponível")

        resultado = service.buscar_flashcards_pendentes(uuid4())

        assert resultado[0]["conteudo"] is None

    def test_mesmo_s3_chave_e_baixado_apenas_uma_vez(self, service, revisao_repo, s3_service):
        item1 = _item(s3_chave="chave-compartilhada.json", item_ref="card_001")
        item2 = _item(s3_chave="chave-compartilhada.json", item_ref="card_002")
        revisao_repo.buscar_pendentes_hoje.return_value = [item1, item2]
        s3_service.download_json.return_value = [
            {"item_ref": "card_001", "pergunta": "P1"}, {"item_ref": "card_002", "pergunta": "P2"},
        ]

        resultado = service.buscar_flashcards_pendentes(uuid4())

        assert len(resultado) == 2
        s3_service.download_json.assert_called_once()


class TestAvaliar:
    def test_avaliar_cartao_com_sucesso_atualiza_estado(self, service, revisao_repo, spaced_repetition):
        revisao_repo.buscar_por_id.return_value = {
            "fator_facilidade": 2.5, "intervalo_atual": 1, "repeticoes": 0,
        }
        spaced_repetition.avaliar.return_value = {
            "fator_facilidade": 2.6, "intervalo_atual": 6, "repeticoes": 1,
            "proxima_revisao": datetime.utcnow(),
        }
        revisao_repo.atualizar_estado.return_value = {"fator_facilidade": 2.6}

        resultado = service.avaliar_cartao(uuid4(), uuid4(), qualidade=5)

        assert resultado["fator_facilidade"] == 2.6

    def test_avaliar_questao_com_sucesso(self, service, revisao_repo, spaced_repetition):
        revisao_repo.buscar_por_id.return_value = {
            "fator_facilidade": 2.5, "intervalo_atual": 1, "repeticoes": 0,
        }
        spaced_repetition.avaliar.return_value = {
            "fator_facilidade": 2.6, "intervalo_atual": 6, "repeticoes": 1,
            "proxima_revisao": datetime.utcnow(),
        }
        revisao_repo.atualizar_estado.return_value = {"fator_facilidade": 2.6}

        resultado = service.avaliar_questao(uuid4(), uuid4(), qualidade=4)

        assert resultado["fator_facilidade"] == 2.6

    def test_avaliar_quando_item_nao_encontrado_levanta_erro(self, service, revisao_repo):
        revisao_repo.buscar_por_id.return_value = None

        with pytest.raises(RevisaoNotFoundError):
            service.avaliar_cartao(uuid4(), uuid4(), qualidade=5)

    def test_avaliar_quando_atualizacao_nao_encontra_item_levanta_erro(
        self, service, revisao_repo, spaced_repetition
    ):
        revisao_repo.buscar_por_id.return_value = {
            "fator_facilidade": 2.5, "intervalo_atual": 1, "repeticoes": 0,
        }
        spaced_repetition.avaliar.return_value = {
            "fator_facilidade": 2.6, "intervalo_atual": 6, "repeticoes": 1,
            "proxima_revisao": datetime.utcnow(),
        }
        revisao_repo.atualizar_estado.return_value = None

        with pytest.raises(RevisaoNotFoundError):
            service.avaliar_cartao(uuid4(), uuid4(), qualidade=5)


class TestListarLotes:
    def test_flashcards_consulta_tabela_de_cartoes(self, service, revisao_repo):
        usuario_id = uuid4()
        revisao_repo.listar_lotes.return_value = [{"id": uuid4()}]

        resultado = service.listar_lotes(usuario_id, "flashcards")

        revisao_repo.listar_lotes.assert_called_once_with(usuario_id, "cartoes")
        assert len(resultado) == 1

    def test_quizzes_consulta_tabela_de_questoes(self, service, revisao_repo):
        usuario_id = uuid4()

        service.listar_lotes(usuario_id, "quizzes")

        revisao_repo.listar_lotes.assert_called_once_with(usuario_id, "questoes")
