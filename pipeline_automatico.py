import os
import time
from pathlib import Path
import pandas as pd
from create_video_with_effects_backup import VideoCreator
from utils.generador_historias import generar_historia_y_prompts
from utils.file_utils import sanitizar_titulo_para_directorio
import utils.generador_imagenes as generador_imagenes
import utils.generador_historias as generador_historias
import traceback
from typing import Optional
import re

# Configuración
EXCEL_PATH = Path("utils/data/archivo_historias.xlsx")
SHEET_NAME = "Sheet1"
HISTORIAS_DIR = Path("historias")

def procesar_historias_automatico():
    """
    Pipeline automático completo con selección de modo de operación.
    """
    try:
        # --- MENÚ DE SELECCIÓN DE MODO ---
        print("\n" + "="*60)
        print("🤖 SELECCIONA EL MODO DE OPERACIÓN 🤖")
        print("="*60)
        print("1. Automático Total (Genera todo lo que falte: Historia, Imágenes y Video)")
        print("2. Generar Imágenes y Video (Asume que la historia y prompts ya existen)")
        print("3. Generar solo Video (Asume que la historia, prompts e imágenes ya existen)")
        print("4. Manual (Genera solo historia y prompts)")

        modo_operacion = ""
        while modo_operacion not in ["1", "2", "3", "4"]:
            modo_operacion = input("Elige una opción (1, 2, 3, o 4): ")

        # --- PREGUNTAR POR SUBTÍTULOS ---
        sub_choice = input("\n🤔 ¿Deseas agregar subtítulos al video? (s/n, por defecto 'n' para no): ").lower().strip()
        add_subtitles = sub_choice == 's'
        if add_subtitles:
            print("   ✅ Se generará el video con subtítulos incrustados.")
        else:
            print("   ☑️ Se generará el video SIN subtítulos.")

        # --- PREGUNTAR POR SERVICIO DE IMÁGENES (Solo si es necesario) ---
        modo_imagenes = ""
        if modo_operacion in ["1", "2"]:
            print("\n--- Elige el servicio de generación de imágenes ---")
            print("1. Leonardo.ai (Nube, alta calidad)")
            print("2. Hugging Face - FLUX.1 (Nube, lento)")
            print("3. Stable Diffusion (Local, gratis)")
            print("4. Vertex AI (Google, máxima calidad, ~$0.05/video)")
            while modo_imagenes not in ["1", "2", "3", "4"]:
                modo_imagenes = input("Elige un servicio (1, 2, 3, 4): ")

        # --- PREGUNTAR MÉTODO DE ORDENACIÓN DE IMÁGENES (si se va a generar video) ---
        sort_method = 'name' # Por defecto, para el modo automático total
        if modo_operacion in ["2", "3"]:
            print("\n--- ¿Cómo ordenar las imágenes para el video? ---")
            print("1. Por nombre (ej: 1.jpg, imagen_2.png)")
            print("2. Por fecha de modificación (del más antiguo al más reciente)")
            choice = ""
            while choice not in ["1", "2"]:
                choice = input("Elige una opción (por defecto '1'): ") or "1"
            if choice == "2":
                sort_method = 'date'

        # --- PROCESAR HISTORIAS ---
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        # El estado a buscar depende del modo
        col_estado = 'estado_del_video' if modo_operacion == '3' else 'estado_de_las_imágenes'
        historias_pendientes = df[df[col_estado].str.lower() == 'pendiente']

        if historias_pendientes.empty:
            print("✅ No hay historias pendientes para el modo seleccionado.")
            return

        for idx, row in historias_pendientes.iterrows():
            titulo = row['titulo']
            print(f"\n🎯 PROCESANDO: {titulo} (Modo: {modo_operacion})")
            
            historia_dir = HISTORIAS_DIR / sanitizar_titulo_para_directorio(titulo)
            prompts_path = historia_dir / "prompts.txt"
            parrafos_path = historia_dir / "parrafos.txt"
            historia_generada = False

            def archivo_existe_y_no_vacio(path):
                return path.exists() and path.stat().st_size > 0

            # --- NODO 1: Historia y Prompts ---
            if modo_operacion in ["1", "2", "4"]:
                print("\n📝 NODO 1: Verificando historia y prompts...")
                if archivo_existe_y_no_vacio(prompts_path) and archivo_existe_y_no_vacio(parrafos_path):
                    print("   ✅ Historia y prompts ya existen y no están vacíos.")
                    if modo_operacion == "4":
                        df.loc[idx, 'estado_de_las_imágenes'] = 'realizada'
                        print("   📊 Excel actualizado: estado_de_las_imágenes = realizada (archivos ya existentes)")
                else:
                    if not archivo_existe_y_no_vacio(parrafos_path):
                        if parrafos_path.exists():
                            print("   ⚠️ 'parrafos.txt' existe pero está vacío. Se volverá a generar.")
                        else:
                            print("   ⚠️ 'parrafos.txt' no existe. Se generará.")
                    if not archivo_existe_y_no_vacio(prompts_path):
                        if prompts_path.exists():
                            print("   ⚠️ 'prompts.txt' existe pero está vacío. Se volverá a generar.")
                        else:
                            print("   ⚠️ 'prompts.txt' no existe. Se generará.")
                    print("   ⚙️ Generando historia y prompts...")
                    generar_historia_y_prompts(titulo)
                    historia_generada = True

                # Volver a calcular la ruta después de generar los archivos
                historia_dir = HISTORIAS_DIR / sanitizar_titulo_para_directorio(titulo)
                prompts_path = historia_dir / "prompts.txt"
                parrafos_path = historia_dir / "parrafos.txt"

                if archivo_existe_y_no_vacio(prompts_path) and archivo_existe_y_no_vacio(parrafos_path):
                    with open(prompts_path, 'r', encoding='utf-8') as f:
                        prompts = [p.strip() for p in f.read().split('\n') if p.strip()]
                    # Si estamos en modo 4 y se generó la historia, marcar como realizada
                    if modo_operacion == "4" and historia_generada:
                        df.loc[idx, 'estado_de_las_imágenes'] = 'realizada'
                        print("   📊 Excel actualizado: estado_de_las_imágenes = realizada")
                else:
                    print(f"   ❌ Error: No se pudo generar o encontrar 'prompts.txt' y 'parrafos.txt' para '{titulo}'. Saltando historia.")
                    continue

                if modo_operacion == "4": # Modo Manual termina aquí
                    print("   ✅ Proceso Manual finalizado.")
                    continue

            # --- NODO 2: Generador de Imágenes ---
            if modo_operacion in ["1", "2"]:
                print("\n🖼️ NODO 2: Generando imágenes...")
                # ... (Lógica para llamar a Leonardo, Hugging Face, o SD basada en modo_imagenes)
                # Esta lógica se mantiene como la original
                exito_imagenes = False
                if modo_imagenes == "1": # Leonardo
                    from utils.generar_imagenes_leonardo import generar_imagenes_para_historia
                    exito_imagenes = generar_imagenes_para_historia(historia_dir, prompts, fallback_enabled=True)
                elif modo_imagenes == "2": # Hugging Face
                    from utils.generar_imagenes_huggingface import generar_imagenes_para_historia_flux
                    exito_imagenes = generar_imagenes_para_historia_flux(historia_dir, prompts)
                elif modo_imagenes == "3": # Stable Diffusion
                    from utils.generar_imagenes_stable_diffusion import get_sd_generator
                    LORA_POR_DEFECTO = "ponyRealism_V23ULTRA"
                    sd_generator = get_sd_generator(lora_name=LORA_POR_DEFECTO)
                    rutas_imagenes = sd_generator.generar_imagenes(prompts, historia_dir)
                    exito_imagenes = len(rutas_imagenes) == len(prompts)
                elif modo_imagenes == "4": # Vertex AI
                    from utils.generar_imagenes_vertex import generar_imagenes_para_historia_vertex
                    exito_imagenes = generar_imagenes_para_historia_vertex(historia_dir, prompts)
                
                if not exito_imagenes:
                    print(f"   ❌ Error crítico: No se pudieron generar las imágenes. Saltando.")
                    continue
                df.loc[idx, 'estado_de_las_imágenes'] = 'realizada'


            # --- NODO 3: Generador de Video ---
            print("\n🎬 NODO 3: Creando video...")
            creator = VideoCreator(
                historia_dir, 
                overwrite=True, 
                add_subtitles=add_subtitles,
                sort_method=sort_method
            )
            video_creado_con_exito = creator.create_video()
            
            if video_creado_con_exito:
                print("   ✅ Video procesado exitosamente.")
                df.loc[idx, 'estado_del_video'] = 'realizado'
                df.to_excel(EXCEL_PATH, index=False)
                print("   📊 Estado actualizado en Excel.")
            else:
                print(f"   ❌ Fallo en la creación del video para '{titulo}'. El estado no se actualizará.")

        # Guardar el Excel si hubo cambios en modo 4
        if modo_operacion == "4":
            df.to_excel(EXCEL_PATH, index=False)
            print("\n💾 Excel actualizado con historias realizadas en modo manual.")

    except Exception as e:
        print(f"❌ Error en el pipeline automático: {e}")
        traceback.print_exc()

def sanitizar_titulo_para_directorio(titulo: str) -> str:
    return re.sub(r'[^\w\s-]', '', titulo).strip().replace(' ', '_')

def generar_historia_y_prompts(titulo):
    # Wrapper para la función existente
    from utils.generador_historias import generar_historia_y_prompts as gen_func
    return gen_func(titulo)

def seleccionar_historia_pendiente() -> Optional[str]:
    """Lee el Excel y devuelve el título de la primera historia pendiente."""
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        # Asegurarse de que la columna 'video' exista y manejar posibles errores de tipo
        if 'video' not in df.columns:
            print(f"❌ Error: La columna 'video' no se encuentra en el archivo Excel.")
            return None
            
        df_pendientes = df[df['video'].str.lower() == 'pendiente']
        
        if df_pendientes.empty:
            print("\n✨ No hay historias pendientes para crear videos.")
            return None
        
        # Devuelve el título de la primera historia pendiente
        return df_pendientes.iloc[0]['titulo']
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo Excel en {EXCEL_PATH}")
        return None
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel: {e}")
        return None

def marcar_historia_como_realizada(titulo: str):
    """Marca una historia como 'realizada' en el archivo Excel."""
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        # Encontrar el índice de la fila que corresponde al título
        indices = df.index[df['titulo'] == titulo].tolist()
        if indices:
            idx = indices[0]
            df.loc[idx, "video"] = "realizada"
            df.to_excel(EXCEL_PATH, index=False)
            print(f"\n📊 Estado actualizado a 'realizada' para: {titulo}")
        else:
            print(f"⚠️ No se encontró la historia '{titulo}' en el Excel para marcarla como realizada.")
    except Exception as e:
        print(f"❌ Error al actualizar el archivo Excel: {e}")

def crear_videos_pendientes():
    """
    Busca en el Excel historias con imágenes listas pero sin video
    y crea los videos correspondientes de forma automática.
    """
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        # Asegurarse de que las columnas de estado son string para comparaciones seguras
        df['estado_de_las_imágenes'] = df['estado_de_las_imágenes'].astype(str)
        df['estado_del_video'] = df['estado_del_video'].astype(str)
        
        videos_pendientes = df[
            (df['estado_de_las_imágenes'].str.lower() == 'realizada') & 
            (df['estado_del_video'].str.lower() == 'pendiente')
        ]
        
        if videos_pendientes.empty:
            print("\n✅ No hay videos pendientes de creación con imágenes ya realizadas.")
            return

        print(f"\n🎬 Creando {len(videos_pendientes)} videos pendientes...")

        for idx, row in videos_pendientes.iterrows():
            titulo = row['titulo']
            print(f"\n--- Creando video para: {titulo} ---")
            
            historia_dir = HISTORIAS_DIR / sanitizar_titulo_para_directorio(titulo)
            
            if not historia_dir.exists():
                print(f"❌ Error: El directorio '{historia_dir}' no existe. Saltando esta historia.")
                continue
            
            try:
                creator = VideoCreator(historia_dir, overwrite=True)
                # NOTA: Esta función no es interactiva. Asumimos que no queremos subtítulos
                # o podríamos añadir un parámetro a la función si fuera necesario.
                # Por ahora, se mantiene el comportamiento por defecto (subtítulos ON).
                # Para ser consistentes, lo pasaremos a False.
                creator = VideoCreator(historia_dir, overwrite=True, add_subtitles=False)
                video_creado_con_exito = creator.create_video()
                
                if video_creado_con_exito:
                    print(f"✨ Video creado exitosamente para {titulo}")
                    # Actualizar el estado en el dataframe y guardar
                    df.at[idx, 'estado_del_video'] = 'realizado'
                    df.to_excel(EXCEL_PATH, index=False)
                    print(f"✅ Estado del video para '{titulo}' actualizado a 'realizado' en Excel.")
                else:
                    print(f"❌ Fallo al crear el video para '{titulo}'. No se actualizará el estado.")
                
            except Exception as e:
                print(f"❌ Error al crear el video para '{titulo}': {e}")

    except Exception as e:
        print(f"❌ Error al procesar la creación de videos pendientes: {e}")

if __name__ == "__main__":
    procesar_historias_automatico() 