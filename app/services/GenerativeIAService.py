from google import genai
from google.genai import errors
import os
import time
import logging

logger = logging.getLogger(__name__)

class GenerativeIAService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.modelo = os.getenv("MODELO_GEMINI", "models/gemini-2.0-flash")

    def gerar_resumo(self, texto_extraido: str) -> str:
        TAMANHO_MAXIMO_CHUNK = 10000  
        ESPERA_ENTRE_CHUNKS = 5       
        MAX_RETENTATIVAS = 3

        chunks = [texto_extraido[i:i + TAMANHO_MAXIMO_CHUNK] for i in range(0, len(texto_extraido), TAMANHO_MAXIMO_CHUNK)]
        resumos_parciais = []

        logger.info(f"Texto dividido em {len(chunks)} chunk(s). Iniciando processamento com {self.modelo}...")

        for index, chunk in enumerate(chunks):
            prompt = f"Você é um tutor acadêmico. Faça um resumo estruturado da seguinte parte de um documento:\n{chunk}"
            
            sucesso = False
            tentativas = 0
            
            while not sucesso and tentativas < MAX_RETENTATIVAS:
                try:
                    logger.info(f"Enviando chunk {index + 1}/{len(chunks)}...")
                    
                    response = self.client.models.generate_content(
                        model=self.modelo,
                        contents=prompt
                    )
                    
                    resumos_parciais.append(response.text)
                    sucesso = True
                    
                    if index < len(chunks) - 1:
                        time.sleep(ESPERA_ENTRE_CHUNKS)

                except (errors.ClientError, errors.ServerError) as e:
                    # Captura tanto limite de cota (429) quanto erro de servidor/demanda (503)
                    erro_msg = str(e).upper()
                    if "429" in erro_msg or "RESOURCE_EXHAUSTED" in erro_msg or "503" in erro_msg or "UNAVAILABLE" in erro_msg:
                        espera = 30 * (tentativas + 1)
                        logger.warning(f"IA ocupada ou limite atingido. Pausando por {espera}s (Tentativa {tentativas + 1}/{MAX_RETENTATIVAS}).")
                        time.sleep(espera)
                        tentativas += 1
                    else:
                        logger.error(f"Erro crítico na API: {e}")
                        raise e

            if not sucesso:
                raise RuntimeError(f"Falha ao gerar resumo após {MAX_RETENTATIVAS} tentativas.")

        logger.info("Consolidando resumo final.")
        return "\n\n--- Continuação ---\n\n".join(resumos_parciais)