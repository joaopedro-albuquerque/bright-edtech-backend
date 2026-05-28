import google.genai as genai
import os

class GenerativeIAService:
    def __init__(self):
        # A chave de API deve vir do seu .env
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # O modelo flash-2.0 é o ideal para processar grandes volumes de texto (1M tokens) gratuitamente
        self.model = genai.Client().models.GenerativeModel('gemini-2.0-flash')

    def gerar_resumo(self, texto_extraido: str) -> str:
        prompt = f"""
        Você é um tutor acadêmico. Faça um resumo estruturado em tópicos do seguinte documento:
        
        {texto_extraido}
        """
        response = self.model.generate_content(prompt)
        return response.text