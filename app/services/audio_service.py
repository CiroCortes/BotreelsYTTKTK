from pathlib import Path
import json
from app.network.google_tts_client import GoogleTTSClient

class AudioService:
    """
    Servicio para la generación y validación de audios de voz a partir de texto.
    Utiliza GoogleTTSClient para la síntesis.
    """
    def __init__(self, creds_path=None):
        self.tts_client = GoogleTTSClient(creds_path)

    def generar_audios_para_historia(self, historia_dir: Path, parrafos: list[dict]):
        """Genera archivos de voz para cada párrafo usando GoogleTTSClient."""
        audio_dir = historia_dir / "audios"
        audio_dir.mkdir(exist_ok=True)
        audios_faltantes = []
        for parrafo in parrafos:
            numero = parrafo['numero']
            texto = parrafo['texto']
            output_file = f"voz_parrafo_{numero}.mp3"
            output_path = audio_dir / output_file
            if not output_path.exists():
                audios_faltantes.append((numero, texto))
        if not audios_faltantes:
            print("✅ Todos los archivos de audio ya existen.")
            return True
        print(f"📝 Generando {len(audios_faltantes)} archivos de audio faltantes...")
        for numero, texto in audios_faltantes:
            output_file = f"voz_parrafo_{numero}.mp3"
            output_path = audio_dir / output_file
            self.tts_client.sintetizar_texto(texto, output_path)
        print("\n✨ Proceso de síntesis de voz completado")
        return True

    def validar_audios(self, historia_dir: Path, total: int) -> bool:
        """Valida que existan todos los archivos de audio para los párrafos."""
        audio_dir = historia_dir / "audios"
        for idx in range(1, total + 1):
            audio_path = audio_dir / f"voz_parrafo_{idx}.mp3"
            if not audio_path.exists() or audio_path.stat().st_size == 0:
                return False
        return True 