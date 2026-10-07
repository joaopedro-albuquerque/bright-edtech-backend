import io
import json
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from google.genai import errors as genai_errors

from app.core.exceptions import AiGenerationError
from app.services import BedrockService as bedrock_module
from app.services.BedrockService import BedrockService


def _fake_stream_body(payload: dict):
    return io.BytesIO(json.dumps(payload).encode())


def _resposta_gemini(texto: str, prompt_tokens: int, candidates_tokens: int):
    resposta = MagicMock()
    resposta.text = texto
    resposta.usage_metadata.prompt_token_count = prompt_tokens
    resposta.usage_metadata.candidates_token_count = candidates_tokens
    return resposta


def _client_error(message="erro genérico"):
    return ClientError({"Error": {"Code": "ValidationException", "Message": message}}, "InvokeModel")


def _throttling_client_error():
    return ClientError({"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}}, "InvokeModel")


def _genai_throttling_error():
    return genai_errors.ClientError(
        429, {"error": {"message": "RESOURCE_EXHAUSTED", "status": "RESOURCE_EXHAUSTED"}}
    )


def _genai_fatal_error():
    return genai_errors.ClientError(400, {"error": {"message": "bad request", "status": "INVALID_ARGUMENT"}})


@pytest.fixture
def service(mocker):
    mocker.patch("app.services.BedrockService.boto3.client")
    mocker.patch("app.services.BedrockService.genai.Client")
    mocker.patch("app.services.BedrockService.time.sleep")
    return BedrockService()


class TestCarregarGeminiApiKey:
    def test_retorna_valor_do_ssm_quando_disponivel(self, mocker):
        mock_boto_client = mocker.patch("app.services.BedrockService.boto3.client")
        mock_boto_client.return_value.get_parameter.return_value = {"Parameter": {"Value": "chave-ssm"}}

        resultado = bedrock_module._carregar_gemini_api_key()

        assert resultado == "chave-ssm"

    def test_cai_para_env_var_quando_ssm_falha(self, mocker, monkeypatch):
        mocker.patch("app.services.BedrockService.boto3.client", side_effect=_client_error())
        monkeypatch.setenv("GEMINI_API_KEY", "chave-env")

        resultado = bedrock_module._carregar_gemini_api_key()

        assert resultado == "chave-env"


class TestInvocarBedrock:
    def test_sucesso_na_primeira_tentativa(self, service):
        service.bedrock_client.invoke_model.return_value = {
            "body": _fake_stream_body({"content": [{"text": "resposta"}], "usage": {"input_tokens": 10, "output_tokens": 5}})
        }

        texto, tokens = service._invocar_bedrock("modelo-x", "prompt", "chunk", 100, 3, 0, 1)

        assert texto == "resposta"
        assert tokens == 15

    def test_erro_nao_throttling_propaga_client_error_imediatamente(self, service):
        service.bedrock_client.invoke_model.side_effect = _client_error("acesso negado")

        with pytest.raises(ClientError):
            service._invocar_bedrock("modelo-x", "prompt", "chunk", 100, 3, 0, 1)

    def test_throttling_tenta_novamente_e_sucede_na_segunda_tentativa(self, service):
        sucesso = {
            "body": _fake_stream_body({"content": [{"text": "ok"}], "usage": {"input_tokens": 1, "output_tokens": 1}})
        }
        service.bedrock_client.invoke_model.side_effect = [_throttling_client_error(), sucesso]

        texto, tokens = service._invocar_bedrock("modelo-x", "prompt", "chunk", 100, 3, 0, 1)

        assert texto == "ok"
        assert service.bedrock_client.invoke_model.call_count == 2

    def test_throttling_esgota_tentativas_e_propaga_client_error(self, service):
        service.bedrock_client.invoke_model.side_effect = _throttling_client_error()

        with pytest.raises(ClientError):
            service._invocar_bedrock("modelo-x", "prompt", "chunk", 100, 3, 0, 1)

        assert service.bedrock_client.invoke_model.call_count == 3

    def test_max_retentativas_zero_levanta_ai_generation_error(self, service):
        with pytest.raises(AiGenerationError, match="após 0 tentativas"):
            service._invocar_bedrock("modelo-x", "prompt", "chunk", 100, 0, 0, 1)


class TestInvocarGemini:
    def test_sucesso_na_primeira_tentativa(self, service):
        resposta = _resposta_gemini("texto gerado", prompt_tokens=10, candidates_tokens=5)
        service.gemini_client.models.generate_content.return_value = resposta

        texto, tokens = service._invocar_gemini("prompt", "chunk", 100, 3, 0, 1)

        assert texto == "texto gerado"
        assert tokens == 15

    def test_erro_fatal_propaga_imediatamente(self, service):
        service.gemini_client.models.generate_content.side_effect = _genai_fatal_error()

        with pytest.raises(genai_errors.ClientError):
            service._invocar_gemini("prompt", "chunk", 100, 3, 0, 1)

    def test_throttling_tenta_novamente_e_sucede(self, service):
        resposta = _resposta_gemini("ok", prompt_tokens=1, candidates_tokens=1)
        service.gemini_client.models.generate_content.side_effect = [_genai_throttling_error(), resposta]

        texto, tokens = service._invocar_gemini("prompt", "chunk", 100, 3, 0, 1)

        assert texto == "ok"

    def test_throttling_esgota_tentativas_e_propaga_erro(self, service):
        service.gemini_client.models.generate_content.side_effect = _genai_throttling_error()

        with pytest.raises(genai_errors.ClientError):
            service._invocar_gemini("prompt", "chunk", 100, 3, 0, 1)

    def test_max_retentativas_zero_levanta_ai_generation_error(self, service):
        with pytest.raises(AiGenerationError, match="após 0 tentativas"):
            service._invocar_gemini("prompt", "chunk", 100, 0, 0, 1)


class TestInvocarModelo:
    def test_usa_bedrock_quando_disponivel_em_chunk_unico(self, service, mocker):
        mocker.patch.object(service, "_invocar_bedrock", return_value=("resposta bedrock", 20))

        texto, tokens, modelo = service._invocar_modelo("modelo-bedrock", "system", "texto curto", 100)

        assert texto == "resposta bedrock"
        assert tokens == 20
        assert modelo == "modelo-bedrock"

    def test_faz_fallback_para_gemini_quando_bedrock_falha(self, service, mocker):
        mocker.patch.object(service, "_invocar_bedrock", side_effect=Exception("bedrock indisponível"))
        mocker.patch.object(service, "_invocar_gemini", return_value=("resposta gemini", 5))

        texto, tokens, modelo = service._invocar_modelo("modelo-bedrock", "system", "texto", 100)

        assert texto == "resposta gemini"
        assert modelo == service.modelo_fallback

    def test_levanta_ai_generation_error_quando_bedrock_e_gemini_falham(self, service, mocker):
        mocker.patch.object(service, "_invocar_bedrock", side_effect=Exception("bedrock down"))
        mocker.patch.object(service, "_invocar_gemini", side_effect=Exception("gemini down"))

        with pytest.raises(AiGenerationError, match="Falha ao invocar IA"):
            service._invocar_modelo("modelo-bedrock", "system", "texto", 100)

    def test_concatena_respostas_de_multiplos_chunks(self, service, mocker):
        invocar_spy = mocker.patch.object(
            service, "_invocar_bedrock", side_effect=[("parte1", 10), ("parte2", 10)]
        )
        texto_grande = "a" * 25000

        texto, tokens, _ = service._invocar_modelo("modelo-bedrock", "system", texto_grande, 100)

        assert texto == "parte1\n\nparte2"
        assert tokens == 20
        assert invocar_spy.call_count == 2


class TestParsearJsonLista:
    def test_parseia_json_puro(self, service):
        resultado = service._parsear_json_lista('[{"item_ref": "a"}]')

        assert resultado == [{"item_ref": "a"}]

    def test_parseia_json_envolto_em_code_fence_com_marcador_json(self, service):
        resultado = service._parsear_json_lista('```json\n[{"item_ref": "a"}]\n```')

        assert resultado == [{"item_ref": "a"}]

    def test_parseia_json_envolto_em_code_fence_sem_marcador(self, service):
        resultado = service._parsear_json_lista('```\n[{"item_ref": "a"}]\n```')

        assert resultado == [{"item_ref": "a"}]

    def test_json_invalido_levanta_ai_generation_error(self, service):
        with pytest.raises(AiGenerationError, match="formato inválido"):
            service._parsear_json_lista("isto não é json")


class TestGerarConteudo:
    def test_gerar_resumo_delega_para_invocar_modelo_com_modelo_de_resumo(self, service, mocker):
        mocker.patch.object(service, "_invocar_modelo", return_value=("texto", 10, "modelo-x"))

        texto, tokens, modelo = service.gerar_resumo("conteudo", "cornell", 5, "formal")

        assert texto == "texto"
        chamada = service._invocar_modelo.call_args
        assert chamada.kwargs["modelo_bedrock"] == service.modelo_resumo

    def test_gerar_flashcards_delega_e_parseia_json(self, service, mocker):
        mocker.patch.object(service, "_invocar_modelo", return_value=('[{"item_ref": "card_001"}]', 10, "modelo-x"))

        cartoes, tokens, modelo = service.gerar_flashcards("texto", 5, "facil")

        assert cartoes == [{"item_ref": "card_001"}]

    def test_gerar_quiz_delega_e_parseia_json(self, service, mocker):
        mocker.patch.object(service, "_invocar_modelo", return_value=('[{"item_ref": "q_001"}]', 10, "modelo-x"))

        questoes, tokens, modelo = service.gerar_quiz("texto", 5, "dificil")

        assert questoes == [{"item_ref": "q_001"}]
