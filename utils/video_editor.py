from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from PIL import Image
from pathlib import Path
import random
import numpy as np

class VideoEditor:
    def __init__(self, historia_dir: Path):
        self.historia_dir = historia_dir
        self.music_dir = Path("musica")
        
    def _resize_image(self, image_path, target_width=1080):
        """Redimensiona una imagen usando PIL."""
        with Image.open(image_path) as img:
            # Calcular nueva altura manteniendo el aspect ratio
            aspect_ratio = img.height / img.width
            target_height = int(target_width * aspect_ratio)
            
            # Redimensionar
            img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Calcular dimensiones para crop vertical (9:16)
            target_height_9_16 = int(target_width * 16/9)
            
            # Si la imagen es más alta que lo necesario, hacer crop
            if target_height > target_height_9_16:
                top = (target_height - target_height_9_16) // 2
                bottom = top + target_height_9_16
                img_cropped = img_resized.crop((0, top, target_width, bottom))
            else:
                # Si es más baja, agregar bordes negros
                new_img = Image.new('RGB', (target_width, target_height_9_16), (0, 0, 0))
                paste_y = (target_height_9_16 - target_height) // 2
                new_img.paste(img_resized, (0, paste_y))
                img_cropped = new_img
                
            return np.array(img_cropped)
    
    def _cargar_imagenes(self) -> list:
        """Carga las imágenes en orden numérico."""
        imagenes = []
        for i in range(1, 12):  # 11 imágenes
            img_path = self.historia_dir / f"imagen_{i}.png"
            if img_path.exists():
                img_array = self._resize_image(img_path)
                imagenes.append(img_array)
            else:
                raise FileNotFoundError(f"No se encontró la imagen: {img_path}")
        return imagenes
    
    def _crear_clip_subtitulo(self, texto: str, duracion: float) -> TextClip:
        """Crea un clip de texto para los subtítulos."""
        return (TextClip(texto, 
                        fontsize=70, 
                        color='white',
                        font='Arial',
                        size=(1000, None),
                        method='caption')
                .set_duration(duracion)
                .set_position(('center', 'bottom'))
                .margin(bottom=100))
    
    def crear_video(self, output_path: str = None) -> None:
        """Crea el video final combinando imágenes, voz y música."""
        if output_path is None:
            output_path = str(self.historia_dir / "video_final.mp4")
            
        # Cargar recursos
        imagenes = self._cargar_imagenes()
        audio_voz = AudioFileClip(str(self.historia_dir / "voz.mp3"))
        
        # Calcular duración para cada imagen
        duracion_total = audio_voz.duration
        duracion_por_imagen = duracion_total / len(imagenes)
        
        # Crear secuencia de imágenes
        video = ImageSequenceClip(imagenes, durations=[duracion_por_imagen] * len(imagenes))
        video = video.set_position('center')
        
        # Agregar audio
        musica = AudioFileClip(str(random.choice(list(self.music_dir.glob("*.mp3")))))
        musica = musica.subclip(0, min(musica.duration, duracion_total))
        
        audio_final = CompositeAudioClip([audio_voz, musica])
        video = video.set_audio(audio_final)
        
        print("\nℹ️ Iniciando la exportación del video...")
        print(f"   - Duración total: {duracion_total:.2f} segundos")
        print(f"   - Imágenes: {len(imagenes)}")
        
        # Exportar video
        video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium',
            bitrate="8000k"
        )
        
        print(f"\n✅ Video creado exitosamente: {output_path}")
        print("   Verifica que:")
        print("   - Las imágenes se muestren correctamente")
        print("   - El audio se escuche claramente")