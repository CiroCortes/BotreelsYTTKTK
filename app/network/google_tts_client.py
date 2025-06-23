from google.cloud import texttospeech
from pathlib import Path
import os

class GoogleTTSClient:
    def __init__(self, creds_path=None):
        if creds_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(Path(creds_path))
        self.tts_client = texttospeech.TextToSpeechClient()

    def sintetizar_texto(self, texto, output_path, language_code="es-ES", voice_name="es-ES-Standard-B", gender=texttospeech.SsmlVoiceGender.MALE):
        synthesis_input = texttospeech.SynthesisInput(text=texto)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=gender
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        print(f"✅ Audio generado: {output_path}") 