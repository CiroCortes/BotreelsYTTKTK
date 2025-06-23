import google.generativeai as genai
from pathlib import Path
from app.network.prompt_utils import calcular_prompts_necesarios

class GeminiClient:
    def __init__(self, api_key_path=None):
        if api_key_path is None:
            api_key_path = Path("config/credentials/gemini_api_key.txt")
        with open(api_key_path, 'r') as f:
            api_key = f.read().strip()
        if not api_key:
            raise ValueError("La clave API de Gemini está vacía")
        genai.configure(api_key=api_key)
        self.model_text = genai.GenerativeModel("gemini-1.5-flash")

    def generar_respuesta(self, prompt: str, parrafos: list[str] = None) -> str:
        try:
            print("\n🤖 Enviando prompt a Gemini...")
            if parrafos:
                num_prompts = calcular_prompts_necesarios(parrafos)
                prompt = f"{prompt}\n\nGenera exactamente {num_prompts} prompts para las imágenes, uno por cada segmento de 5-6 segundos."
            response = self.model_text.generate_content(prompt)
            if not response.text:
                raise ValueError("La respuesta de Gemini está vacía")
            print("✅ Respuesta recibida de Gemini")
            return response.text
        except Exception as e:
            print(f"❌ Error al generar la respuesta: {str(e)}")
            return None 