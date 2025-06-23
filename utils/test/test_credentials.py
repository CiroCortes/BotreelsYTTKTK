from google.cloud import speech
import os
from pathlib import Path

def test_credentials():
    try:
        # Configurar credenciales
        creds_path = "config/credentials/n8n-yt-458902-7993e2a59b32.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(Path(creds_path))
        
        # Intentar crear el cliente
        client = speech.SpeechClient()
        print("✅ Credenciales verificadas correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al verificar credenciales: {str(e)}")
        return False

if __name__ == "__main__":
    test_credentials() 