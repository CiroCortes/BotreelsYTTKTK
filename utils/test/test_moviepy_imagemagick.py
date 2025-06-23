import os
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
from moviepy.editor import TextClip

# Prueba de creación de un clip de texto
txt_clip = TextClip("Test MoviePy + ImageMagick", fontsize=70, color='white')
txt_clip.save_frame("test_textclip.png")
print("✅ ¡Test completado! Revisa el archivo test_textclip.png")