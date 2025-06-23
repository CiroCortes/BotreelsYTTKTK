import pandas as pd
from pathlib import Path
import os
from PIL import Image
import io
import google.generativeai as genai
import time
import re
import requests
from typing import Optional, Tuple
import utils.generar_imagenes_stable_diffusion as sd_generator_module
import utils.generar_imagenes_leonardo as leonardo_generator_module
from utils.file_utils import sanitizar_titulo_para_directorio

# Configuración de rutas y constantes
EXCEL_PATH = Path("utils/data/archivo_historias.xlsx")
SHEET_NAME = "Sheet1"
DIRECTORIO_BASE = "imagenes_generadas"
MAX_REINTENTOS = 3
TIEMPO_ESPERA_INICIAL = 25  # segundos (ajustado según experiencia con GoogleFX)
TIEMPO_ESPERA_MAXIMO = 40   # segundos (tiempo máximo razonable)
TIEMPO_ENTRE_REINTENTOS = 5  # segundos

def limpiar_nombre_archivo(texto: str) -> str:
    """Limpia el texto para usarlo como nombre de archivo."""
    texto_limpio = re.sub(r'[^a-zA-Z0-9\s-]', '', texto)
    texto_limpio = texto_limpio.strip()
    texto_limpio = re.sub(r'\s+', '_', texto_limpio)
    return texto_limpio[:50]

def configurar_api():
    """Configura la API de Google"""
    API_KEY = "AIzaSyDb4PDjVbO2ZEXA5SprdgeDejK-IMe4RwE"
    genai.configure(api_key=API_KEY)

def crear_directorio_historia(titulo: str) -> str:
    """Crea un directorio para la historia si no existe."""
    if not os.path.exists(DIRECTORIO_BASE):
        os.makedirs(DIRECTORIO_BASE)
    
    nombre_directorio = sanitizar_titulo_para_directorio(titulo)
    ruta_directorio = os.path.join(DIRECTORIO_BASE, nombre_directorio)
    
    if not os.path.exists(ruta_directorio):
        os.makedirs(ruta_directorio)
        print(f"\nDirectorio creado: {ruta_directorio}")
    
    return ruta_directorio

def esperar_y_verificar_imagen(response, tiempo_espera: int = TIEMPO_ESPERA_INICIAL) -> Optional[bytes]:
    """
    Espera y verifica que la imagen esté lista.
    Implementa espera exponencial si es necesario.
    """
    tiempo_total = 0
    tiempo_actual = tiempo_espera

    while tiempo_total < TIEMPO_ESPERA_MAXIMO:
        try:
            # Intentar obtener la imagen
            imagen_bytes = response.image
            if imagen_bytes:
                return imagen_bytes
        except Exception as e:
            print(f"Esperando la imagen... ({tiempo_total}s transcurridos)")
        
        # Esperar antes del siguiente intento
        time.sleep(tiempo_actual)
        tiempo_total += tiempo_actual
        # Incrementar tiempo de espera (pero no más del máximo)
        tiempo_actual = min(tiempo_actual * 1.5, TIEMPO_ESPERA_MAXIMO - tiempo_total)

    return None

def generar_imagen(prompt: str, titulo: str, numero_parrafo: int, directorio_historia: str) -> Tuple[str, float]:
    """
    Genera una imagen usando Gemini y la guarda en formato JPG 9:16.
    Retorna la ruta de la imagen y el tiempo que tomó generarla.
    """
    tiempo_inicio = time.time()

    for intento in range(MAX_REINTENTOS):
        try:
            print(f"\nGenerando imagen {numero_parrafo}/11 para '{titulo}'")
            print(f"Intento {intento + 1}/{MAX_REINTENTOS}")
            
            # Configurar y generar
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.9,
                    "top_p": 1,
                    "top_k": 32,
                    "max_output_tokens": 2048,
                }
            )
            
            # Esperar y verificar que la imagen esté lista
            print("Esperando que la imagen se genere...")
            imagen_bytes = esperar_y_verificar_imagen(response)
            
            if not imagen_bytes:
                raise Exception("Tiempo de espera agotado para la generación de imagen")
            
            # Procesar y guardar la imagen
            imagen_pil = Image.open(io.BytesIO(imagen_bytes))
            imagen_pil = imagen_pil.resize((1080, 1920), Image.Resampling.LANCZOS)
            
            # Crear nombre y guardar
            prompt_corto = limpiar_nombre_archivo(prompt[:30])
            nombre_archivo = f"parrafo_{numero_parrafo:02d}_{prompt_corto}.jpg"
            ruta_completa = os.path.join(directorio_historia, nombre_archivo)
            
            imagen_pil.save(ruta_completa, "JPEG", quality=95)
            tiempo_total = time.time() - tiempo_inicio
            
            print(f"✓ Imagen guardada exitosamente: {nombre_archivo}")
            print(f"  Tiempo de generación: {tiempo_total:.1f} segundos")
            
            return ruta_completa, tiempo_total
            
        except Exception as e:
            print(f"Error en intento {intento + 1}: {str(e)}")
            if intento < MAX_REINTENTOS - 1:
                print(f"Reintentando en {TIEMPO_ENTRE_REINTENTOS} segundos...")
                time.sleep(TIEMPO_ENTRE_REINTENTOS)
            else:
                print(f"❌ No se pudo generar la imagen después de {MAX_REINTENTOS} intentos")
                return None, time.time() - tiempo_inicio

def procesar_imagenes():
    """Procesa los prompts del Excel y genera las imágenes secuencialmente"""
    try:
        configurar_api()
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        
        # Filtrar solo las historias con imágenes pendientes, excluyendo las marcadas como 'no hacer'
        df_pendientes = df[
            (df['imagen'].str.lower() == 'pendiente') & 
            (df['estado'].str.lower() != 'no hacer')
        ]
        total_historias = len(df_pendientes)
        
        if total_historias == 0:
            print("\n✨ No hay historias pendientes para generar imágenes.")
            return 0
        
        historias_procesadas = 0
        tiempo_total_proceso = 0
        
        for idx, row in df_pendientes.iterrows():
            titulo = row.get("titulo")
            if not titulo:
                continue
            
            historias_procesadas += 1
            print(f"\n{'='*50}")
            print(f"Procesando historia {historias_procesadas}/{total_historias}: {titulo}")
            print(f"{'='*50}")
            
            directorio_historia = crear_directorio_historia(titulo)
            imagenes_generadas = 0
            tiempo_historia = 0
            exito = True
            
            # Procesar cada prompt secuencialmente
            for i in range(1, 12):
                col_prompt = f"prompt{i}"
                prompt = row.get(col_prompt)
                
                if prompt and isinstance(prompt, str) and prompt.strip():
                    ruta_imagen, tiempo_generacion = generar_imagen(prompt, titulo, i, directorio_historia)
                    if ruta_imagen:
                        imagenes_generadas += 1
                        tiempo_historia += tiempo_generacion
                    else:
                        exito = False
                        break
            
            # Actualizar el estado en el Excel solo si todas las imágenes se generaron correctamente
            if exito and imagenes_generadas > 0:
                df.at[idx, 'imagen'] = 'realizada'
                print("\n✅ Estado actualizado a 'realizada' en el Excel")
            elif not exito:
                print("\n❌ No se actualizó el estado debido a errores en la generación")
            
            tiempo_total_proceso += tiempo_historia
            print(f"\nResumen para '{titulo}':")
            print(f"✓ {imagenes_generadas} imágenes generadas de 11 intentadas")
            print(f"⏱ Tiempo total para esta historia: {tiempo_historia/60:.1f} minutos")
            print(f"📁 Guardadas en: {directorio_historia}")
        
        # Guardar cambios en el Excel
        df.to_excel(EXCEL_PATH, index=False)
        print("\n💾 Cambios guardados en el archivo Excel")
            
    except Exception as e:
        print(f"\n❌ Error general en el procesamiento: {e}")
        return tiempo_total_proceso
    
    return tiempo_total_proceso

def iniciar_generacion_imagenes():
    """Función principal que será llamada desde main.py"""
    print("\n🎨 Iniciando generación de imágenes...")
    print("Este proceso puede tomar varios minutos por historia.")
    print(f"Tiempo de espera inicial por imagen: {TIEMPO_ESPERA_INICIAL} segundos")
    inicio = time.time()
    
    tiempo_total = procesar_imagenes()
    
    print(f"\n✨ Generación de imágenes completada")
    print(f"⏱ Tiempo total del proceso: {tiempo_total/60:.1f} minutos")
    print(f"⏱ Tiempo total con overhead: {(time.time() - inicio)/60:.1f} minutos")

def generar_imagenes_para_historia(historia_path, prompts, service='stable_diffusion', lora_name=None):
    """
    Despachador principal para la generación de imágenes.
    Elige el servicio (local o en la nube) y delega la tarea.

    Args:
        historia_path (Path): Ruta al directorio de la historia.
        prompts (list): Lista de prompts para generar las imágenes.
        service (str): 'stable_diffusion' o 'leonardo'.
        lora_name (str, optional): Nombre del LoRA a usar si el servicio es 'stable_diffusion'.
    """
    print(f"\n🚀 Usando el servicio de generación de imágenes: {service.replace('_', ' ').title()}")

    if service == 'stable_diffusion':
        # Llama a la función de generación de Stable Diffusion
        sd_generator_module.generar_imagenes_para_historia(
            historia_dir=historia_path,
            prompts=prompts,
            lora_name=lora_name
        )
    elif service == 'leonardo':
        # Llama a la función de generación de Leonardo.AI
        leonardo_generator_module.generar_imagenes_para_historia(
            historia_dir=historia_path,
            prompts=prompts
        )
    else:
        raise ValueError(f"Servicio de generación desconocido: {service}")

if __name__ == "__main__":
    iniciar_generacion_imagenes()