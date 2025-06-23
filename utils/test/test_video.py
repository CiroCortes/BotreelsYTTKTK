from pathlib import Path
from utils.video_editor import VideoEditor

def crear_video_enoc():
    # Ruta de la historia
    historia_dir = Path("historias/la_historia_de_enoc")
    
    print("\n🎬 Iniciando generación del video...")
    print(f"📁 Directorio de la historia: {historia_dir}")
    
    try:
        # Crear el editor de video
        editor = VideoEditor(historia_dir)
        
        # Generar el video
        editor.crear_video()
        
    except Exception as e:
        print(f"\n❌ Error durante la generación del video: {str(e)}")
        raise e

if __name__ == "__main__":
    crear_video_enoc() 