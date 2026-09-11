import json
import logging
import os
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

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


class BedrockService:
    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1")),
        )
        self.modelo_resumo = os.getenv("BEDROCK_MODEL_SUMMARY", "anthropic.claude-sonnet-5")
        self.modelo_extracao = os.getenv("BEDROCK_MODEL_EXTRACT", "anthropic.claude-haiku-4-5-20251001-v1:0")

    def gerar_resumo(self, texto: str, formato: str, nivel_conhecimento: int, tom: str) -> tuple[str, int, str]:
        prompt_base = SYSTEM_PROMPTS_RESUMO.get(formato, SYSTEM_PROMPTS_RESUMO["resumo_executivo"])
        system_prompt = (
            f"{prompt_base}\n\n"
            f"Nível de conhecimento do leitor no assunto (escala 0-10, onde 0 é totalmente "
            f"leigo e 10 é especialista): {nivel_conhecimento}. Ajuste a profundidade técnica "
            f"de acordo.\n"
            f"Tom/linguagem desejado: {tom}."
        )

        texto_gerado, tokens_utilizados = self._invocar_modelo(
            modelo=self.modelo_resumo,
            system_prompt=system_prompt,
            user_content=texto,
            max_tokens=4096,
        )
        return texto_gerado, tokens_utilizados, self.modelo_resumo

    def gerar_flashcards(self, texto: str, quantidade: int = 10) -> tuple[list, int, str]:
        system_prompt = (
            f"Você extrai conceitos-chave de um texto e gera exatamente {quantidade} "
            "flashcards de pergunta/resposta para revisão espaçada. Responda APENAS com "
            "um JSON válido, sem texto adicional, no formato: "
            '[{"item_ref": "card_001", "pergunta": "...", "resposta": "..."}, ...]'
        )

        resposta, tokens_utilizados = self._invocar_modelo(
            modelo=self.modelo_extracao,
            system_prompt=system_prompt,
            user_content=texto,
            max_tokens=4096,
        )
        return self._parsear_json_lista(resposta), tokens_utilizados, self.modelo_extracao

    def gerar_quiz(self, texto: str, quantidade: int = 10) -> tuple[list, int, str]:
        system_prompt = (
            f"Você extrai conceitos-chave de um texto e gera exatamente {quantidade} "
            "questões de múltipla escolha (4 alternativas) para revisão espaçada. "
            "Responda APENAS com um JSON válido, sem texto adicional, no formato: "
            '[{"item_ref": "q_001", "pergunta": "...", "alternativas": ["a", "b", "c", "d"], '
            '"resposta_correta": "a"}, ...]'
        )

        resposta, tokens_utilizados = self._invocar_modelo(
            modelo=self.modelo_extracao,
            system_prompt=system_prompt,
            user_content=texto,
            max_tokens=4096,
        )
        return self._parsear_json_lista(resposta), tokens_utilizados, self.modelo_extracao

    # Helpers
    def _invocar_modelo(self, modelo: str, system_prompt: str, user_content: str, max_tokens: int) -> tuple[str, int]:
        TAMANHO_MAXIMO_CHUNK = 20000
        MAX_RETENTATIVAS = 3

        chunks = [user_content[i:i + TAMANHO_MAXIMO_CHUNK] for i in range(0, len(user_content), TAMANHO_MAXIMO_CHUNK)] or [""]
        respostas_parciais = []
        tokens_totais = 0

        for index, chunk in enumerate(chunks):
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": chunk}],
            }

            tentativas = 0
            sucesso = False

            while not sucesso and tentativas < MAX_RETENTATIVAS:
                try:
                    logger.info(f"Invocando Bedrock ({modelo}), chunk {index + 1}/{len(chunks)}...")
                    response = self.client.invoke_model(
                        modelId=modelo,
                        body=json.dumps(body),
                    )
                    payload = json.loads(response["body"].read())

                    texto_resposta = "".join(
                        bloco.get("text", "") for bloco in payload.get("content", [])
                    )
                    respostas_parciais.append(texto_resposta)

                    uso = payload.get("usage", {})
                    tokens_totais += uso.get("input_tokens", 0) + uso.get("output_tokens", 0)

                    sucesso = True
                except (BotoCoreError, ClientError) as exc:
                    erro_msg = str(exc)
                    if "ThrottlingException" in erro_msg or "TooManyRequests" in erro_msg:
                        espera = 5 * (tentativas + 1)
                        logger.warning(f"Bedrock throttled. Aguardando {espera}s (tentativa {tentativas + 1}).")
                        time.sleep(espera)
                        tentativas += 1
                    else:
                        logger.error(f"Erro crítico ao invocar Bedrock: {exc}")
                        raise RuntimeError(f"Falha ao invocar Bedrock: {exc}") from exc

            if not sucesso:
                raise RuntimeError(f"Falha ao invocar Bedrock após {MAX_RETENTATIVAS} tentativas.")

        return "\n\n".join(respostas_parciais), tokens_totais

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
            raise ValueError("A IA retornou um formato inválido. Tente novamente.") from exc
