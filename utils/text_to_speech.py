from google.cloud import speech
from google.cloud import texttospeech
import os
from pathlib import Path
import json
import time
from datetime import datetime
from app.network.google_tts_client import GoogleTTSClient

class AudioProcessor:
    def __init__(self, historia_dir, creds_path=None):
        self.historia_dir = Path(historia_dir)
        
        # Configurar credenciales
        if creds_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(Path(creds_path))
            print(f"✅ Usando credenciales de: {creds_path}")
        else:
            print("⚠️ No se especificó ruta de credenciales. Asegúrate de configurar GOOGLE_APPLICATION_CREDENTIALS")
        
        self.client = speech.SpeechClient()
        self.tts_client = GoogleTTSClient(creds_path)
        self.tiempo_espera = 5  # segundos entre peticiones
        
        # Configuración de reconocimiento de voz
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            language_code="es-ES",
            enable_automatic_punctuation=True,
            model="default"
        )

    def procesar_audio(self, audio_path, numero_parrafo):
        """Procesa un archivo de audio y lo transcribe."""
        try:
            # Crear directorio para transcripciones si no existe
            transcripciones_dir = self.historia_dir / "transcripciones"
            transcripciones_dir.mkdir(exist_ok=True)
            
            # Leer el archivo de audio
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            # Configurar el audio
            audio = speech.RecognitionAudio(content=content)
            
            # Registrar tiempo de inicio
            inicio = datetime.now()
            print(f"⏳ Iniciando transcripción del audio {numero_parrafo}...")
            
            # Realizar la transcripción
            response = self.client.recognize(config=self.config, audio=audio)
            
            # Calcular tiempo de procesamiento
            tiempo_procesamiento = (datetime.now() - inicio).total_seconds()
            print(f"⏱️ Tiempo de procesamiento: {tiempo_procesamiento:.1f} segundos")
            
            # Guardar transcripción
            output_file = f"transcripcion_{numero_parrafo}.txt"
            output_path = transcripciones_dir / output_file
            
            # Extraer el texto transcrito
            texto_transcrito = ""
            for result in response.results:
                texto_transcrito += result.alternatives[0].transcript + "\n"
            
            # Guardar en archivo
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(texto_transcrito)
            
            print(f"✅ Transcripción guardada: {output_file}")
            return texto_transcrito
            
        except Exception as e:
            print(f"❌ Error al procesar audio {numero_parrafo}: {str(e)}")
            return None

    def procesar_audios(self):
        """Procesa todos los archivos de audio de la historia."""
        try:
            # Cargar control de párrafos
            control_file = self.historia_dir / "control_parrafos.json"
            with open(control_file, 'r', encoding='utf-8') as f:
                info_parrafos = json.load(f)
            
            # Obtener archivos de audio
            audio_dir = self.historia_dir / "audios"
            if not audio_dir.exists():
                print("❌ No se encontró el directorio de audios")
                return False
                
            audio_files = sorted(audio_dir.glob("voz_parrafo_*.mp3"))
            total_audios = len(audio_files)
            
            if total_audios == 0:
                print("❌ No se encontraron archivos de audio para procesar")
                return False
                
            print(f"\n📝 Total de archivos de audio a procesar: {total_audios}")
            
            # Procesar cada audio
            for i, audio_file in enumerate(audio_files, 1):
                numero = int(audio_file.stem.split('_')[-1])
                
                print(f"\n🎙️ Procesando audio {numero} ({i}/{total_audios})...")
                texto = self.procesar_audio(audio_file, numero)
                
                if texto:
                    # Actualizar el JSON con la transcripción
                    for parrafo in info_parrafos['parrafos']:
                        if parrafo['numero'] == numero:
                            parrafo['transcripcion'] = texto
                            break
                    
                    # Esperar antes de la siguiente petición
                    if i < total_audios:
                        print(f"⏳ Esperando {self.tiempo_espera} segundos antes de la siguiente petición...")
                        time.sleep(self.tiempo_espera)
                else:
                    print(f"⚠️ No se pudo procesar el audio {numero}")
            
            # Guardar JSON actualizado
            with open(control_file, 'w', encoding='utf-8') as f:
                json.dump(info_parrafos, f, indent=2, ensure_ascii=False)
            
            print("\n✨ Proceso de transcripción completado")
            return True
            
        except Exception as e:
            print(f"\n❌ Error en el proceso: {str(e)}")
            return False

    def process_story(self):
        try:
            control_file = self.historia_dir / "control_parrafos.json"
            with open(control_file, 'r', encoding='utf-8') as f:
                info_parrafos = json.load(f)
            audio_dir = self.historia_dir / "audios"
            audio_dir.mkdir(exist_ok=True)
            audios_faltantes = []
            for parrafo in info_parrafos['parrafos']:
                numero = parrafo['numero']
                output_file = f"voz_parrafo_{numero}.mp3"
                output_path = audio_dir / output_file
                if not output_path.exists():
                    audios_faltantes.append((numero, parrafo['texto']))
            if not audios_faltantes:
                print("✅ Todos los archivos de audio ya existen.")
                return True
            print(f"📝 Generando {len(audios_faltantes)} archivos de audio faltantes...")
            for numero, texto in audios_faltantes:
                output_file = f"voz_parrafo_{numero}.mp3"
                output_path = audio_dir / output_file
                self.tts_client.sintetizar_texto(texto, output_path)
                if numero < len(info_parrafos['parrafos']):
                    print(f"⏳ Esperando 30 segundos antes de la siguiente petición...")
                    time.sleep(30)
            print("\n✨ Proceso de síntesis de voz completado")
            return True
        except Exception as e:
            print(f"\n❌ Error en el proceso: {str(e)}")
            return False

if __name__ == "__main__":
    # Ejemplo de uso
    historia_dir = Path("historias/el_diluvio_realidad_o_mito")
    creds_path = "config/credentials/n8n-yt-458902-7993e2a59b32.json"  # Ruta correcta
    processor = AudioProcessor(historia_dir, creds_path)
    processor.process_story()  # Cambiado a process_story para generar audios 