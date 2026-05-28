from google import genai
import os

class GenerativeIAService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def gerar_resumo(self, texto_extraido: str) -> str:
        prompt = f"""
        Você é um tutor acadêmico. Faça um resumo estruturado em tópicos do seguinte documento:
        
        {texto_extraido}
        """
        
        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        
        return response.text