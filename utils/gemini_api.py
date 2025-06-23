from app.network.gemini_client import GeminiClient

gemini = GeminiClient()

def generar_respuesta(prompt: str, parrafos: list[str] = None) -> str:
    return gemini.generar_respuesta(prompt, parrafos)
