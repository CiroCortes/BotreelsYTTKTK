from pathlib import Path
import os
from utils.file_utils import sanitizar_titulo_para_directorio
from app.models.video import Video
# from create_video_with_effects_backup import VideoCreator  # Importa tu clase real de creación de video

class VideoService:
    """
    Servicio para la creación y validación de videos a partir de imágenes, audio, etc.
    Orquesta el flujo y está preparado para delegar a un cliente externo si se requiere.
    """
    def procesar_videos_pendientes(self, historias: list[str]):
        """Procesa todos los videos pendientes para una lista de historias."""
        for titulo in historias:
            print(f"\n[NODO VIDEO] Procesando video para: {titulo}")
            if self.validar_video(titulo):
                print("   ✅ Video ya existe y es válido.")
                continue
            try:
                video = self.crear_video_para_historia(titulo)
                if self.validar_video(titulo):
                    print("   ✅ Video creado correctamente.")
                else:
                    print("   ❌ Error: No se pudo validar el video generado para:", titulo)
            except Exception as e:
                print(f"   ❌ Error creando video para '{titulo}': {e}")

    def crear_video_para_historia(self, titulo: str) -> Video:
        """
        Placeholder para la creación de video. Aquí se debe delegar a un cliente de red o microservicio si se implementa.
        Actualmente simula la creación del video final.
        """
        titulo_limpio = sanitizar_titulo_para_directorio(titulo)
        historia_dir = Path("historias") / titulo_limpio
        historia_dir.mkdir(parents=True, exist_ok=True)
        # Aquí deberías llamar a tu clase real de creación de video o a un cliente externo
        # Por ahora, solo simula la existencia del archivo
        video_path = historia_dir / "video_final.mp4"
        if not video_path.exists():
            with open(video_path, "wb") as f:
                f.write(b"")  # Crea un archivo vacío como placeholder
        print(f"   [Simulación] Video creado para: {historia_dir}")
        return Video.from_path(video_path)

    def validar_video(self, titulo: str) -> bool:
        """Valida si el video existe y es correcto para la historia dada."""
        titulo_limpio = sanitizar_titulo_para_directorio(titulo)
        historia_dir = Path("historias") / titulo_limpio
        video_path = historia_dir / "video_final.mp4"
        return video_path.exists() and video_path.stat().st_size > 0

    def cargar_video(self, titulo: str) -> Video:
        """Carga el video existente para una historia y retorna un modelo Video."""
        titulo_limpio = sanitizar_titulo_para_directorio(titulo)
        historia_dir = Path("historias") / titulo_limpio
        video_path = historia_dir / "video_final.mp4"
        if not video_path.exists() or video_path.stat().st_size == 0:
            raise FileNotFoundError("No se encontró el video generado.")
        return Video.from_path(video_path) 