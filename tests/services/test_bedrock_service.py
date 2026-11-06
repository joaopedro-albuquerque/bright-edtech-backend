import base64
import io
import json
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from google.genai import errors as genai_errors

from app.core.exceptions import AiGenerationError
from app.services import BedrockService as bedrock_module
from app.services.BedrockService import BedrockService


PDF = b"%PDF-1.4 conteudo"


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

        texto, tokens = service._invocar_bedrock("modelo-x", "prompt", PDF, "instrucao", 100, 3)

        assert texto == "resposta"
        assert tokens == 15

    def test_erro_nao_throttling_propaga_client_error_imediatamente(self, service):
        service.bedrock_client.invoke_model.side_effect = _client_error("acesso negado")

        with pytest.raises(ClientError):
            service._invocar_bedrock("modelo-x", "prompt", PDF, "instrucao", 100, 3)

    def test_throttling_tenta_novamente_e_sucede_na_segunda_tentativa(self, service):
        sucesso = {
            "body": _fake_stream_body({"content": [{"text": "ok"}], "usage": {"input_tokens": 1, "output_tokens": 1}})
        }
        service.bedrock_client.invoke_model.side_effect = [_throttling_client_error(), sucesso]

        texto, tokens = service._invocar_bedrock("modelo-x", "prompt", PDF, "instrucao", 100, 3)

        assert texto == "ok"
        assert service.bedrock_client.invoke_model.call_count == 2

    def test_throttling_esgota_tentativas_e_propaga_client_error(self, service):
        service.bedrock_client.invoke_model.side_effect = _throttling_client_error()

        with pytest.raises(ClientError):
            service._invocar_bedrock("modelo-x", "prompt", PDF, "instrucao", 100, 3)

        assert service.bedrock_client.invoke_model.call_count == 3

    def test_max_retentativas_zero_levanta_ai_generation_error(self, service):
        with pytest.raises(AiGenerationError, match="após 0 tentativas"):
            service._invocar_bedrock("modelo-x", "prompt", PDF, "instrucao", 100, 0)


class TestInvocarGemini:
    def test_sucesso_na_primeira_tentativa(self, service):
        resposta = _resposta_gemini("texto gerado", prompt_tokens=10, candidates_tokens=5)
        service.gemini_client.models.generate_content.return_value = resposta

        texto, tokens = service._invocar_gemini("prompt", PDF, "instrucao", 100, 3)

        assert texto == "texto gerado"
        assert tokens == 15

    def test_erro_fatal_propaga_imediatamente(self, service):
        service.gemini_client.models.generate_content.side_effect = _genai_fatal_error()

        with pytest.raises(genai_errors.ClientError):
            service._invocar_gemini("prompt", PDF, "instrucao", 100, 3)

    def test_throttling_tenta_novamente_e_sucede(self, service):
        resposta = _resposta_gemini("ok", prompt_tokens=1, candidates_tokens=1)
        service.gemini_client.models.generate_content.side_effect = [_genai_throttling_error(), resposta]

        texto, tokens = service._invocar_gemini("prompt", PDF, "instrucao", 100, 3)

        assert texto == "ok"

    def test_throttling_esgota_tentativas_e_propaga_erro(self, service):
        service.gemini_client.models.generate_content.side_effect = _genai_throttling_error()

        with pytest.raises(genai_errors.ClientError):
            service._invocar_gemini("prompt", PDF, "instrucao", 100, 3)

    def test_max_retentativas_zero_levanta_ai_generation_error(self, service):
        with pytest.raises(AiGenerationError, match="após 0 tentativas"):
            service._invocar_gemini("prompt", PDF, "instrucao", 100, 0)


class TestInvocarModelo:
    def test_usa_bedrock_quando_disponivel(self, service, mocker):
        mocker.patch.object(service, "_invocar_bedrock", return_value=("resposta bedrock", 20))

        texto, tokens, modelo = service._invocar_modelo("modelo-bedrock", "system", PDF, "instrucao", 100)

        assert texto == "resposta bedrock"
        assert tokens == 20
        assert modelo == "modelo-bedrock"

    def test_faz_fallback_para_gemini_quando_bedrock_falha(self, service, mocker):
        mocker.patch.object(service, "_invocar_bedrock", side_effect=Exception("bedrock indisponível"))
        mocker.patch.object(service, "_invocar_gemini", return_value=("resposta gemini", 5))

        texto, tokens, modelo = service._invocar_modelo("modelo-bedrock", "system", PDF, "instrucao", 100)

        assert texto == "resposta gemini"
        assert modelo == service.modelo_fallback

    def test_levanta_ai_generation_error_quando_bedrock_e_gemini_falham(self, service, mocker):
        mocker.patch.object(service, "_invocar_bedrock", side_effect=Exception("bedrock down"))
        mocker.patch.object(service, "_invocar_gemini", side_effect=Exception("gemini down"))

        with pytest.raises(AiGenerationError, match="Falha ao invocar IA"):
            service._invocar_modelo("modelo-bedrock", "system", PDF, "instrucao", 100)

    def test_faz_uma_unica_chamada_por_documento_sem_dividir_em_blocos(self, service, mocker):
        invocar = mocker.patch.object(service, "_invocar_bedrock", return_value=("ok", 10))

        service._invocar_modelo("modelo-bedrock", "system", b"x" * 500_000, "instrucao", 100)

        assert invocar.call_count == 1


class TestEnvioDoPdfNativo:
    def test_bedrock_recebe_o_pdf_como_bloco_document_em_base64(self, service):
        service.bedrock_client.invoke_model.return_value = {
            "body": _fake_stream_body({"content": [{"text": "ok"}], "usage": {}})
        }

        service._invocar_bedrock("modelo-x", "prompt", PDF, "instrucao", 100, 3)

        body = json.loads(service.bedrock_client.invoke_model.call_args.kwargs["body"])
        conteudo = body["messages"][0]["content"]
        assert conteudo[0]["type"] == "document"
        assert conteudo[0]["source"] == {
            "type": "base64",
            "media_type": "application/pdf",
            "data": base64.b64encode(PDF).decode("ascii"),
        }
        assert conteudo[1] == {"type": "text", "text": "instrucao"}
        assert body["system"] == "prompt"
        assert body["max_tokens"] == 100

    def test_gemini_recebe_o_pdf_como_parte_com_mime_type_pdf(self, service):
        service.gemini_client.models.generate_content.return_value = _resposta_gemini("ok", 1, 1)

        service._invocar_gemini("prompt", PDF, "instrucao", 100, 3)

        contents = service.gemini_client.models.generate_content.call_args.kwargs["contents"]
        assert contents[0].inline_data.data == PDF
        assert contents[0].inline_data.mime_type == "application/pdf"
        assert contents[1] == "instrucao"


class TestMaxTokensProporcional:
    def test_quantidade_pequena_usa_o_piso(self):
        assert bedrock_module._max_tokens_para_itens(5, bedrock_module.TOKENS_POR_FLASHCARD) == 4096

    def test_quantidade_maxima_de_quiz_excede_o_piso_antigo(self):
        assert bedrock_module._max_tokens_para_itens(50, bedrock_module.TOKENS_POR_QUESTAO) > 4096

    def test_nunca_passa_do_teto(self):
        assert bedrock_module._max_tokens_para_itens(10_000, 1000) == bedrock_module.TOKENS_MAXIMO_SAIDA


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

        texto, tokens, modelo = service.gerar_resumo(PDF, "cornell", 5, "formal")

        assert texto == "texto"
        chamada = service._invocar_modelo.call_args
        assert chamada.kwargs["modelo_bedrock"] == service.modelo_resumo
        assert chamada.kwargs["pdf_bytes"] == PDF

    def test_gerar_resumo_pede_para_considerar_conteudo_visual(self, service, mocker):
        mocker.patch.object(service, "_invocar_modelo", return_value=("texto", 10, "modelo-x"))

        service.gerar_resumo(PDF, "cornell", 5, "formal")

        assert "figuras, gráficos, tabelas" in service._invocar_modelo.call_args.kwargs["system_prompt"]

    def test_gerar_flashcards_delega_e_parseia_json(self, service, mocker):
        mocker.patch.object(service, "_invocar_modelo", return_value=('[{"item_ref": "card_001"}]', 10, "modelo-x"))

        cartoes, tokens, modelo = service.gerar_flashcards(PDF, 5, "facil")

        assert cartoes == [{"item_ref": "card_001"}]
        assert service._invocar_modelo.call_args.kwargs["pdf_bytes"] == PDF

    def test_gerar_quiz_delega_e_parseia_json(self, service, mocker):
        mocker.patch.object(service, "_invocar_modelo", return_value=('[{"item_ref": "q_001"}]', 10, "modelo-x"))

        questoes, tokens, modelo = service.gerar_quiz(PDF, 5, "dificil")

        assert questoes == [{"item_ref": "q_001"}]

    def test_quantidade_maxima_recebe_mais_tokens_de_saida_que_o_limite_antigo(self, service, mocker):
        mocker.patch.object(service, "_invocar_modelo", return_value=("[]", 10, "modelo-x"))

        service.gerar_quiz(PDF, 50, "medio")

        assert service._invocar_modelo.call_args.kwargs["max_tokens"] > 4096


class TestModerarConteudo:
    def _mock_invocar(self, service, mocker, resposta):
        return mocker.patch.object(service, "_invocar_modelo", return_value=(resposta, 10, "modelo"))

    def test_veredito_improprio_retorna_true_e_motivo(self, service, mocker):
        self._mock_invocar(service, mocker, '{"improprio": true, "motivo": "conteúdo sexual explícito"}')

        improprio, motivo = service.moderar_conteudo(PDF)

        assert improprio is True
        assert motivo == "conteúdo sexual explícito"

    def test_veredito_proprio_retorna_false(self, service, mocker):
        self._mock_invocar(service, mocker, '{"improprio": false, "motivo": "material didático"}')

        improprio, _ = service.moderar_conteudo(PDF)

        assert improprio is False

    def test_aceita_resposta_dentro_de_bloco_de_codigo(self, service, mocker):
        self._mock_invocar(service, mocker, '```json\n{"improprio": false, "motivo": ""}\n```')

        improprio, _ = service.moderar_conteudo(PDF)

        assert improprio is False

    def test_usa_o_prompt_de_moderacao_ampla(self, service, mocker):
        invocar = self._mock_invocar(service, mocker, '{"improprio": false, "motivo": ""}')

        service.moderar_conteudo(PDF)

        assert invocar.call_args.kwargs["system_prompt"] == bedrock_module.SYSTEM_PROMPT_MODERACAO

    @pytest.mark.parametrize("categoria", [
        "sexual explícito",
        "violência gráfica",
        "discurso de ódio",
        "atividades ilegais",
    ])
    def test_prompt_cobre_as_categorias_improprias(self, categoria):
        assert categoria in bedrock_module.SYSTEM_PROMPT_MODERACAO

    def test_prompt_preserva_o_material_educativo(self):
        assert "NÃO é impróprio material educativo" in bedrock_module.SYSTEM_PROMPT_MODERACAO

    @pytest.mark.parametrize("resposta", [
        "isso não é json",
        '["improprio"]',
        '{"motivo": "faltou o campo"}',
        '{"improprio": "sim"}',
    ])
    def test_veredito_invalido_levanta_ai_generation_error(self, service, mocker, resposta):
        self._mock_invocar(service, mocker, resposta)

        with pytest.raises(AiGenerationError):
            service.moderar_conteudo(PDF)

    def test_falha_da_ia_propaga_ai_generation_error(self, service, mocker):
        mocker.patch.object(service, "_invocar_modelo", side_effect=AiGenerationError("fora do ar"))

        with pytest.raises(AiGenerationError):
            service.moderar_conteudo(PDF)

    def test_envia_o_pdf_com_prompt_de_moderacao(self, service, mocker):
        mock = self._mock_invocar(service, mocker, '{"improprio": false}')

        service.moderar_conteudo(PDF)

        kwargs = mock.call_args.kwargs
        assert kwargs["pdf_bytes"] == PDF
        assert kwargs["system_prompt"] == bedrock_module.SYSTEM_PROMPT_MODERACAO
        assert kwargs["max_tokens"] == 200

    def test_prompt_de_moderacao_cobre_imagens(self):
        assert "imagens" in bedrock_module.SYSTEM_PROMPT_MODERACAO
