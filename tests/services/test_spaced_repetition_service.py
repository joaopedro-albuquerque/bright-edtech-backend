import math
from datetime import datetime, timedelta

import pytest

from app.services.SpacedRepetitionService import SpacedRepetitionService


@pytest.fixture
def service():
    return SpacedRepetitionService()


@pytest.fixture(autouse=True)
def _tempo_fixo(mocker):
    fixo = datetime(2026, 1, 1, 12, 0, 0)
    mock_datetime = mocker.patch("app.services.SpacedRepetitionService.datetime")
    mock_datetime.utcnow.return_value = fixo
    return fixo


class TestQualidadeBaixaReiniciaProgresso:
    @pytest.mark.parametrize("repeticoes_atual", [0, 1, 5])
    def test_qualidade_menor_que_3_zera_repeticoes_e_intervalo(self, service, repeticoes_atual, _tempo_fixo):
        resultado = service.avaliar(
            fator_facilidade=2.5, intervalo_atual=10, repeticoes=repeticoes_atual, qualidade=2
        )

        assert resultado["repeticoes"] == 0
        assert resultado["intervalo_atual"] == 1
        assert resultado["proxima_revisao"] == _tempo_fixo + timedelta(days=1)


class TestQualidadeAltaAvancaProgresso:
    def test_primeira_repeticao_bem_sucedida_define_intervalo_1(self, service, _tempo_fixo):
        resultado = service.avaliar(fator_facilidade=2.5, intervalo_atual=0, repeticoes=0, qualidade=4)

        assert resultado["intervalo_atual"] == 1
        assert resultado["repeticoes"] == 1

    def test_segunda_repeticao_bem_sucedida_define_intervalo_6(self, service, _tempo_fixo):
        resultado = service.avaliar(fator_facilidade=2.5, intervalo_atual=1, repeticoes=1, qualidade=4)

        assert resultado["intervalo_atual"] == 6
        assert resultado["repeticoes"] == 2

    def test_repeticoes_subsequentes_multiplicam_intervalo_pelo_fator_facilidade(self, service, _tempo_fixo):
        resultado = service.avaliar(fator_facilidade=2.0, intervalo_atual=10, repeticoes=2, qualidade=5)

        assert resultado["intervalo_atual"] == math.ceil(10 * 2.0)
        assert resultado["repeticoes"] == 3
        assert resultado["proxima_revisao"] == _tempo_fixo + timedelta(days=20)


class TestFatorFacilidade:
    def test_fator_facilidade_e_recalculado_sem_ultrapassar_o_minimo_em_qualidade_alta(self, service):
        resultado = service.avaliar(fator_facilidade=2.5, intervalo_atual=1, repeticoes=1, qualidade=5)

        assert resultado["fator_facilidade"] == pytest.approx(2.6)

    def test_fator_facilidade_e_limitado_ao_minimo_quando_qualidade_e_muito_baixa(self, service):
        resultado = service.avaliar(fator_facilidade=1.3, intervalo_atual=1, repeticoes=0, qualidade=0)

        assert resultado["fator_facilidade"] == SpacedRepetitionService.EF_MINIMO
