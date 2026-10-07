import json
import logging
import os
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.core.exceptions import AiGenerationError

logger = logging.getLogger(__name__)

# Tenta Bedrock primeiro; se falhar (ex: ThrottlingException por cota diária de
# tokens esgotada, comum em contas novas), cai automaticamente pro Gemini como
# fallback, pra não travar o desenvolvimento enquanto a cota do Bedrock não sobe.


def _carregar_gemini_api_key() -> str | None:
    """Busca a API key do Gemini no SSM Parameter Store. Executado uma única vez
    no import do módulo. Cai pra variável de ambiente se o SSM não estiver acessível."""
    try:
        region = os.getenv("AWS_REGION", "us-east-1")
        ssm_client = boto3.client("ssm", region_name=region)
        response = ssm_client.get_parameter(
            Name="/brightedtech/gemini/api_key",
            WithDecryption=True,
        )
        logger.info("GEMINI_API_KEY carregada do SSM Parameter Store.")
        return response["Parameter"]["Value"]
    except (BotoCoreError, ClientError) as exc:
        logger.warning(f"Não foi possível carregar GEMINI_API_KEY do SSM, usando fallback de variável de ambiente: {exc}")
        return os.getenv("GEMINI_API_KEY")


_GEMINI_API_KEY = _carregar_gemini_api_key()

SYSTEM_PROMPTS_RESUMO = {
    "resumo_executivo": (
        "Você é um especialista em síntese acadêmica. Extraia os 5-7 tópicos MAIS "
        "IMPORTANTES do texto fornecido em bullet points concisos (máx. 2 linhas por "
        "ponto). Evite detalhes desnecessários. Inclua uma seção 'Palavras-Chave' ao "
        "final. Formato: Markdown."
    ),
    "cornell": (
        "Você é um professor criando notas no formato Cornell. Estruture em: "
        "(1) Perguntas-Gatilho e Notas de Estudo em uma tabela Markdown "
        "'Pergunta | Resposta' com 5-8 linhas; (2) Sumário final de 2-3 linhas. "
        "Formato: Markdown."
    ),
    "fichamento_academico": (
        "Você é um acadêmico criando um fichamento estruturado. Inclua: Tema Central, "
        "3-5 Citações Diretas (com aspas), Metodologia, Conceitos-Chave, Apreciação "
        "Crítica (pontos fortes, limitações, relevância atual) e Palavras-Chave. "
        "Formato: Markdown."
    ),
}

_DESCRICAO_DIFICULDADE = {
    "facil": "Nível de dificuldade: FÁCIL — use definições diretas e recall simples de fatos.",
    "medio": "Nível de dificuldade: MÉDIO — exija aplicação de conceitos, não só memorização literal.",
    "dificil": "Nível de dificuldade: DIFÍCIL — exija análise, síntese ou aplicação em casos/cenários novos.",
}


class BedrockService:
    def __init__(self):
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1")),
        )
        self.modelo_resumo = os.getenv("BEDROCK_MODEL_SUMMARY", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
        self.modelo_extracao = os.getenv("BEDROCK_MODEL_EXTRACT", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

        self.gemini_client = genai.Client(api_key=_GEMINI_API_KEY)
        self.modelo_fallback = os.getenv("GEMINI_MODEL_FALLBACK", "gemini-3.6-flash")

    def gerar_resumo(self, texto: str, formato: str, nivel_conhecimento: int, tom: str) -> tuple[str, int, str]:
        prompt_base = SYSTEM_PROMPTS_RESUMO.get(formato, SYSTEM_PROMPTS_RESUMO["resumo_executivo"])
        system_prompt = (
            f"{prompt_base}\n\n"
            f"Nível de conhecimento do leitor no assunto (escala 0-10, onde 0 é totalmente "
            f"leigo e 10 é especialista): {nivel_conhecimento}. Ajuste a profundidade técnica "
            f"de acordo.\n"
            f"Tom/linguagem desejado: {tom}."
        )

        texto_gerado, tokens_utilizados, modelo_usado = self._invocar_modelo(
            modelo_bedrock=self.modelo_resumo,
            system_prompt=system_prompt,
            user_content=texto,
            max_tokens=4096,
        )
        return texto_gerado, tokens_utilizados, modelo_usado

    def gerar_flashcards(self, texto: str, quantidade: int = 10, dificuldade: str = "medio") -> tuple[list, int, str]:
        system_prompt = (
            f"Você extrai conceitos-chave de um texto e gera exatamente {quantidade} "
            "flashcards de pergunta/resposta para revisão espaçada. "
            f"{_DESCRICAO_DIFICULDADE.get(dificuldade, _DESCRICAO_DIFICULDADE['medio'])} "
            "Responda APENAS com um JSON válido, sem texto adicional, no formato: "
            '[{"item_ref": "card_001", "pergunta": "...", "resposta": "..."}, ...]'
        )

        resposta, tokens_utilizados, modelo_usado = self._invocar_modelo(
            modelo_bedrock=self.modelo_extracao,
            system_prompt=system_prompt,
            user_content=texto,
            max_tokens=4096,
        )
        return self._parsear_json_lista(resposta), tokens_utilizados, modelo_usado

    def gerar_quiz(self, texto: str, quantidade: int = 10, dificuldade: str = "medio") -> tuple[list, int, str]:
        system_prompt = (
            f"Você extrai conceitos-chave de um texto e gera exatamente {quantidade} "
            "questões de múltipla escolha (4 alternativas) para revisão espaçada. "
            f"{_DESCRICAO_DIFICULDADE.get(dificuldade, _DESCRICAO_DIFICULDADE['medio'])} "
            "Responda APENAS com um JSON válido, sem texto adicional, no formato: "
            '[{"item_ref": "q_001", "pergunta": "texto da pergunta", '
            '"alternativas": ["texto completo da alternativa 1", "texto completo da alternativa 2", '
            '"texto completo da alternativa 3", "texto completo da alternativa 4"], '
            '"resposta_correta": "texto completo da alternativa correta"}, ...]. '
            "REGRA OBRIGATÓRIA: o campo resposta_correta deve ser uma cópia EXATA, caractere por "
            "caractere, de um dos itens do array alternativas — nunca uma letra (a/b/c/d), "
            "número, índice ou qualquer forma abreviada."
        )

        resposta, tokens_utilizados, modelo_usado = self._invocar_modelo(
            modelo_bedrock=self.modelo_extracao,
            system_prompt=system_prompt,
            user_content=texto,
            max_tokens=4096,
        )
        return self._parsear_json_lista(resposta), tokens_utilizados, modelo_usado

    # Helpers
    def _invocar_modelo(self, modelo_bedrock: str, system_prompt: str, user_content: str, max_tokens: int) -> tuple[str, int, str]:
        TAMANHO_MAXIMO_CHUNK = 20000
        MAX_RETENTATIVAS = 3

        chunks = [user_content[i:i + TAMANHO_MAXIMO_CHUNK] for i in range(0, len(user_content), TAMANHO_MAXIMO_CHUNK)] or [""]
        respostas_parciais = []
        tokens_totais = 0
        modelo_usado = modelo_bedrock

        for index, chunk in enumerate(chunks):
            try:
                texto_resposta, tokens = self._invocar_bedrock(modelo_bedrock, system_prompt, chunk, max_tokens, MAX_RETENTATIVAS, index, len(chunks))
                respostas_parciais.append(texto_resposta)
                tokens_totais += tokens
            except Exception as exc_bedrock:
                logger.warning(f"Bedrock falhou ({exc_bedrock}). Usando fallback Gemini ({self.modelo_fallback}).")
                try:
                    texto_resposta, tokens = self._invocar_gemini(system_prompt, chunk, max_tokens, MAX_RETENTATIVAS, index, len(chunks))
                    respostas_parciais.append(texto_resposta)
                    tokens_totais += tokens
                    modelo_usado = self.modelo_fallback
                except Exception as exc_gemini:
                    logger.error(f"Fallback Gemini também falhou: {exc_gemini}")
                    raise AiGenerationError(
                        f"Falha ao invocar IA (Bedrock: {exc_bedrock} | Gemini: {exc_gemini})"
                    ) from exc_gemini

        return "\n\n".join(respostas_parciais), tokens_totais, modelo_usado

    def _invocar_bedrock(self, modelo: str, system_prompt: str, chunk: str, max_tokens: int, max_retentativas: int, index: int, total_chunks: int) -> tuple[str, int]:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": chunk}],
        }

        tentativas = 0
        while tentativas < max_retentativas:
            try:
                logger.info(f"Invocando Bedrock ({modelo}), chunk {index + 1}/{total_chunks}...")
                response = self.bedrock_client.invoke_model(
                    modelId=modelo,
                    body=json.dumps(body),
                )
                payload = json.loads(response["body"].read())

                texto_resposta = "".join(
                    bloco.get("text", "") for bloco in payload.get("content", [])
                )
                uso = payload.get("usage", {})
                tokens = uso.get("input_tokens", 0) + uso.get("output_tokens", 0)
                return texto_resposta, tokens
            except (BotoCoreError, ClientError) as exc:
                erro_msg = str(exc)
                if "ThrottlingException" in erro_msg or "TooManyRequests" in erro_msg:
                    if tentativas < max_retentativas - 1:
                        espera = 5 * (tentativas + 1)
                        logger.warning(f"Bedrock throttled. Aguardando {espera}s (tentativa {tentativas + 1}).")
                        time.sleep(espera)
                        tentativas += 1
                        continue
                    raise
                raise

        raise AiGenerationError(f"Falha ao invocar Bedrock após {max_retentativas} tentativas.")

    def _invocar_gemini(self, system_prompt: str, chunk: str, max_tokens: int, max_retentativas: int, index: int, total_chunks: int) -> tuple[str, int]:
        config = genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
        )

        tentativas = 0
        while tentativas < max_retentativas:
            try:
                logger.info(f"Invocando Gemini fallback ({self.modelo_fallback}), chunk {index + 1}/{total_chunks}...")
                response = self.gemini_client.models.generate_content(
                    model=self.modelo_fallback,
                    contents=chunk,
                    config=config,
                )
                uso = response.usage_metadata
                tokens = (uso.prompt_token_count or 0) + (uso.candidates_token_count or 0) if uso else 0
                return response.text or "", tokens
            except (genai_errors.ClientError, genai_errors.ServerError) as exc:
                erro_msg = str(exc).upper()
                if "429" in erro_msg or "RESOURCE_EXHAUSTED" in erro_msg or "503" in erro_msg or "UNAVAILABLE" in erro_msg:
                    if tentativas < max_retentativas - 1:
                        espera = 5 * (tentativas + 1)
                        logger.warning(f"Gemini throttled. Aguardando {espera}s (tentativa {tentativas + 1}).")
                        time.sleep(espera)
                        tentativas += 1
                        continue
                    raise
                raise

        raise AiGenerationError(f"Falha ao invocar Gemini após {max_retentativas} tentativas.")

    def _parsear_json_lista(self, texto_resposta: str) -> list:
        texto_limpo = texto_resposta.strip()
        if texto_limpo.startswith("```"):
            texto_limpo = texto_limpo.strip("`")
            if texto_limpo.startswith("json"):
                texto_limpo = texto_limpo[4:]

        try:
            return json.loads(texto_limpo)
        except json.JSONDecodeError as exc:
            logger.error(f"Falha ao parsear JSON retornado pela IA: {exc}. Conteúdo: {texto_limpo[:500]}")
            raise AiGenerationError("A IA retornou um formato inválido. Tente novamente.") from exc
