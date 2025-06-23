try:
    import moviepy
    print("MoviePy está instalado en:", moviepy.__file__)
    
    from moviepy.editor import VideoFileClip
    print("MoviePy editor importado correctamente")
    
except ImportError as e:
    print("Error al importar:", str(e))
except Exception as e:
    print("Otro error:", str(e)) 