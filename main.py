import os
import sys
from pathlib import Path
import pandas as pd
import pipeline_automatico
# ¡IMPORTANTE! Configura la variable de entorno ANTES de cualquier import de MoviePy o módulos que lo usen
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"

# Ahora sí, importa el resto de módulos
from create_video_with_effects_backup import VideoCreator
from utils.gemini_api import generar_respuesta
from utils.prompt_generator import procesar_prompts, guardar_prompts_en_excel
from utils.video_editor import VideoEditor
import re
import random
import os as os2
import json
import subprocess
from utils.text_to_speech import AudioProcessor
from moviepy.editor import AudioFileClip, concatenate_audioclips
import shutil
from utils.generador_historias import generar_historia_y_prompts
from utils.file_utils import sanitizar_titulo_para_directorio

# Importar VideoCreator desde el script de backup
# Asegúrate de que el bloque __main__ en create_video_with_effects_backup.py esté protegido
try:
    from create_video_with_effects_backup import VideoCreator
    print("✅ Clase VideoCreator importada exitosamente.")
except ImportError:
    print("❌ Error: No se pudo importar la clase VideoCreator de create_video_with_effects_backup.py")
    print("Asegúrate de que el archivo create_video_with_effects_backup.py existe y no tiene errores de sintaxis o ejecución directa.")
    VideoCreator = None # Definir como None para evitar NameError si la importación falla

# Verificar credenciales de Google Cloud al inicio
def verificar_credenciales_google():
    """Verifica que las credenciales de Google Cloud estén configuradas correctamente."""
    # Primero intentar usar la variable de entorno
    credenciales_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Si no está configurada la variable de entorno, usar la ruta por defecto
    if not credenciales_path:
        credenciales_path = str(Path("config/credentials/n8n-yt-458902-7993e2a59b32.json"))
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credenciales_path
        print(f"\nℹ️ Usando credenciales por defecto en: {credenciales_path}")
    
    # Convertir la ruta a Path para verificar existencia
    creds_path = Path(credenciales_path)
    if not creds_path.exists():
        print(f"\n❌ Error: El archivo de credenciales no existe en: {creds_path}")
        print("Por favor, sigue estos pasos:")
        print("1. Descarga tu archivo de credenciales desde Google Cloud Console")
        print("2. Coloca el archivo en una ubicación segura")
        print("3. Configura la variable de entorno GOOGLE_APPLICATION_CREDENTIALS:")
        print("   - En Windows (PowerShell):")
        print('   $env:GOOGLE_APPLICATION_CREDENTIALS="ruta/a/tu/archivo-credenciales.json"')
        print("   - En Windows (CMD):")
        print('   set GOOGLE_APPLICATION_CREDENTIALS=ruta/a/tu/archivo-credenciales.json')
        return False
    
    print(f"\n✅ Credenciales de Google Cloud encontradas en: {creds_path}")
    return True

#----configuracion de la ruta excel ------#

EXCEL_PATH = Path("utils/data/archivo_historias.xlsx")
SHEET_NAME = "Sheet1"  
DURACION_OBJETIVO = 70  # 1.2 minutos en segundos
DURACION_CLIP = 4.5  # Duración de cada clip en segundos
HISTORIAS_DIR = Path("historias")  # Directorio base para todas las historias
MUSICA_DIR = Path("musica/biblic_music")  # Directorio de música bíblica

#----Prompt para la generacion de historias----#
#--- deben ser de aspecto brutal, epico, biblbico, apocaliptico con una frase gancho de impacto al princiio

# PROMPT_BASE eliminado - ahora se usa exclusivamente el de utils/generador_historias.py

#--- funcion para operar el  archivo excel ----#

def historia_a_parrafos( texto: str) -> list[str]:
    #convierte el texto en lista de parrafos no vacios
    return [p.strip() for p in texto.split("|") if p.strip()] 
    
    

       

def renombrar_imagenes_manuales(historia_dir: Path):
    """
    Busca imágenes con nombres numéricos (ej: 1.jpg, 2.png) en el directorio de la historia
    y las renombra al formato esperado por VideoCreator (imagen_1.png, imagen_2.png).
    También convierte las imágenes a formato PNG y elimina los archivos originales.
    """
    print(f"🔄 Buscando imágenes manuales en {historia_dir} para renombrar...")
    renombradas = 0
    
    # Primero buscar imágenes numeradas (1.jpg, 2.jpg, etc.)
    for file_path in historia_dir.iterdir():
        if file_path.is_file():
            name = file_path.stem
            extension = file_path.suffix.lower()
            
            # Verificar si el nombre es numérico y la extensión es de imagen
            if name.isdigit() and extension in ['.jpg', '.jpeg', '.png']:
                new_name = f"imagen_{name}.png"
                new_file_path = historia_dir / new_name
                
                try:
                    # Si el archivo ya existe como PNG, no lo procesamos
                    if new_file_path.exists():
                        print(f"  ⚠️ Ya existe: {new_file_path.name}")
                        continue
                        
                    # Convertir a PNG y eliminar el original
                    if extension != '.png':
                        # Aquí podrías agregar la conversión real de imagen si es necesario
                        # Por ahora solo renombramos
                        file_path.rename(new_file_path)
                        print(f"  ✅ Convertido y renombrado: {file_path.name} -> {new_file_path.name}")
                    else:
                        # Si ya es PNG, solo renombramos
                        file_path.rename(new_file_path)
                        print(f"  ✅ Renombrado: {file_path.name} -> {new_file_path.name}")
                    
                    renombradas += 1
                except Exception as e:
                    print(f"  ❌ Error al procesar {file_path.name}: {str(e)}")

    if renombradas > 0:
        print(f"🔄 Se procesaron {renombradas} imágenes.")
    else:
        print("🔄 No se encontraron imágenes para procesar.")

def crear_directorio_historia(titulo: str) -> Path:
    """
    Crea un directorio para la historia basado en su título y subdirectorios necesarios.
    Limpia el título para usarlo como nombre de directorio.
    """
    # Usar la función de sanitización global
    titulo_limpio = sanitizar_titulo_para_directorio(titulo)
    HISTORIAS_DIR.mkdir(exist_ok=True)
    dir_historia = HISTORIAS_DIR / titulo_limpio
    dir_historia.mkdir(exist_ok=True)
    dir_audios = dir_historia / "audios"
    dir_audios.mkdir(exist_ok=True)
    dir_videos = dir_historia / "videos"
    dir_videos.mkdir(exist_ok=True)
    return dir_historia

def calcular_num_parrafos():
    """Calcula el número de párrafos necesarios para la duración objetivo"""
    duracion_transicion = 0.8  # duración de cada transición
    num_parrafos = int((DURACION_OBJETIVO - (duracion_transicion * (DURACION_OBJETIVO/DURACION_CLIP - 1))) / DURACION_CLIP)
    return max(14, num_parrafos)  # Mínimo 14 párrafos

def guardar_informacion_parrafos(historia_dir, parrafos):
    """Guarda la información de los párrafos en un archivo de control, buscando el nombre de archivo de imagen real."""
    control_file = historia_dir / "control_parrafos.json"
    
    # Crear estructura de datos con información de cada párrafo
    info_parrafos = []
    for idx, parrafo in enumerate(parrafos, 1):
        # Buscar el archivo de imagen real en el directorio (puede ser .jpg o .png)
        imagen_encontrada = None
        for ext in ['.jpg', '.jpeg', '.png']:
            nombre_imagen = f"imagen_{idx}{ext}"
            ruta_imagen = historia_dir / nombre_imagen
            if ruta_imagen.exists():
                imagen_encontrada = nombre_imagen
                break # Encontrado, salir del bucle de extensiones
                
        if imagen_encontrada is None:
            print(f"⚠️ Advertencia: No se encontró imagen para el párrafo {idx} con nombre esperado (imagen_{idx}.jpg/png/jpeg).")
            # Opcional: podrías asignar un nombre por defecto o manejar el error de otra forma
            imagen_encontrada = f"imagen_{idx}.png" # Guardar un nombre por defecto aunque no exista el archivo

        info_parrafos.append({
            "numero": idx,
            "texto": parrafo,
            "imagen": imagen_encontrada, # Usar el nombre de archivo encontrado o por defecto
            "duracion_estimada": len(parrafo.split()) * 0.3  # Estimación aproximada: 0.3 segundos por palabra
        })
    
    # Guardar en archivo JSON
    with open(control_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_parrafos": len(parrafos),
            "parrafos": info_parrafos
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 Información de párrafos guardada en: {control_file}")

def procesar_historia(titulo, parrafos):
    """Procesa una historia completa"""
    try:
        titulo_limpio = sanitizar_titulo_para_directorio(titulo)
        historia_dir = Path("historias") / titulo_limpio
        historia_dir.mkdir(exist_ok=True)
        parrafos_completos = [f"{titulo}\n\n{parrafos[0]}"] + parrafos[1:]
        with open(historia_dir / "parrafos.txt", 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(parrafos_completos))
        num_parrafos = len(parrafos_completos)
        imagenes_faltantes = []
        for i in range(1, num_parrafos + 1):
            imagen_path = historia_dir / f"imagen_{i}.png"
            if not imagen_path.exists():
                imagenes_faltantes.append(i)
        if imagenes_faltantes:
            print(f"\n⚠️ Advertencia: Faltan {len(imagenes_faltantes)} imágenes:")
            for num in imagenes_faltantes:
                print(f"  - imagen_{num}.png")
            print(f"\nPor favor, asegúrate de generar todas las imágenes necesarias.")
        guardar_informacion_parrafos(historia_dir, parrafos_completos)
        prompts = []
        for idx, parrafo in enumerate(parrafos_completos, 1):
            if idx == 1:
                prompt = f"Create a cinematic biblical scene with dramatic lighting and epic atmosphere. The scene should be ultra-realistic with divine glow and apocalyptic elements. Use hyper-detailed textures and 4K resolution. The style should combine Renaissance religious art with modern epic film visuals, inspired by Zack Snyder and Caravaggio. The scene should be shot on an ultra high-definition digital cinema camera with volumetric lighting, deep shadows, and celestial illumination. The composition should be vertical (9:16 aspect ratio) and include: A dramatic title scene for '{titulo}' with divine elements and apocalyptic atmosphere, followed by: {parrafo}"
            else:
                prompt = f"Create a cinematic biblical scene with dramatic lighting and epic atmosphere. The scene should be ultra-realistic with divine glow and apocalyptic elements. Use hyper-detailed textures and 4K resolution. The style should combine Renaissance religious art with modern epic film visuals, inspired by Zack Snyder and Caravaggio. The scene should be shot on an ultra high-definition digital cinema camera with volumetric lighting, deep shadows, and celestial illumination. The composition should be vertical (9:16 aspect ratio) and include: {parrafo}"
            prompts.append(prompt)
        with open(historia_dir / "prompts.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(prompts))
        print(f"\n✅ Historia procesada y guardada en: {historia_dir}")
        print(f"📊 Resumen:")
        print(f"   - Título: {titulo}")
        print(f"   - Total de párrafos: {num_parrafos}")
        print(f"   - Imágenes generadas: {num_parrafos - len(imagenes_faltantes)}")
        print(f"   - Imágenes faltantes: {len(imagenes_faltantes)}")
        return historia_dir, prompts
    except Exception as e:
        print(f"\n❌ Error al procesar la historia: {str(e)}")
        return None, None

def procesar_excel():
    """Lee el Excel y obtiene las historias pendientes de video."""
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        # Filtrar por estado_del_video pendiente pero mantener todas las filas
        df_pendientes = df[df['estado_del_video'].str.lower() == 'pendiente'].copy()
        
        if df_pendientes.empty:
            print("\n✨ No hay historias pendientes para crear videos.")
            return None, None
        
        print(f"\n📽️ Se encontraron {len(df_pendientes)} historias pendientes de video.")
        return df_pendientes, df  # Retornar tanto las pendientes como el dataframe completo
        
    except Exception as e:
        print(f"\n❌ Error al leer el Excel: {str(e)}")
        return None, None

def guardar_en_excel(df, idx, historia, prompts, es_generada_ahora: bool = False):
    """Guarda la historia y prompts en el Excel solo si fueron generados ahora."""
    try:
        # Solo guardar historia y prompts si fueron generados en esta ejecución
        if es_generada_ahora:
            # Guardar historia
            df.at[idx, "historia_para_prompt"] = historia # Cambiado a historia_para_prompt
            
            # Limpiar columnas de prompts existentes
            for i in range(1, 31): # Limpiar hasta prompt30
                col_name = f"prompt{i}"
                if col_name in df.columns:
                    df.at[idx, col_name] = None
                    
            # Guardar prompts en columnas separadas (hasta 30)
            for i, prompt in enumerate(prompts[:30], 1):
                col_name = f"prompt{i}"
                if col_name not in df.columns:
                    # Si la columna no existe, la creamos (puede que necesites ejecutar esto una vez manualmente o adaptar la creación del excel)
                    df[col_name] = None
                df.at[idx, col_name] = prompt
            
            print("\n💾 Historia y prompts (recién generados) guardados en el Excel")
        else:
            print("\n💾 No se guardaron historia ni prompts en el Excel (existían previamente)")
        
        # Siempre guardar los cambios en el Excel (incluso si solo se actualizó el estado u otra columna)
        df.to_excel(EXCEL_PATH, index=False)
        print("\n💾 Cambios en el DataFrame guardados en el Excel")
        
    except Exception as e:
        print(f"❌ Error al guardar en Excel: {str(e)}")

def main():
    """Punto de entrada principal de la aplicación."""
    # ¡IMPORTANTE! Configura la variable de entorno ANTES de cualquier import de MoviePy
    os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
    
    # Verificar credenciales al inicio
    if not verificar_credenciales_google():
        exit()
    
    # Iniciar el pipeline principal
    pipeline_automatico.procesar_historias_automatico()

if __name__ == "__main__":
    main()









