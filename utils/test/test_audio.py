from pathlib import Path
from pydub import AudioSegment
import os

def ajustar_volumen_audio():
    # Ruta del archivo de audio
    audio_path = Path("historias/la_historia_de_enoc/voz.mp3")
    output_path = Path("historias/la_historia_de_enoc/voz_30.mp3")
    
    print("\n🎵 Ajustando volumen del audio...")
    print(f"📁 Archivo de audio: {audio_path}")
    
    try:
        # Cargar el audio
        audio = AudioSegment.from_mp3(str(audio_path))
        
        # Ajustar volumen al 30%
        volumen_reducido = audio - 10.5  # -10.5 dB es aproximadamente 30% del volumen original
        
        # Guardar el audio modificado
        volumen_reducido.export(str(output_path), format="mp3")
        
        print(f"✅ Audio procesado guardado en: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento del audio: {str(e)}")
        raise e

if __name__ == "__main__":
    ajustar_volumen_audio() 