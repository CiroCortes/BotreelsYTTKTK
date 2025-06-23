import base64
from pathlib import Path
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.oauth2 import service_account
import os

def generar_imagen_vertex(
    project_id: str,
    location: str,
    prompt: str,
    output_path: Path,
    negative_prompt: str = "blurry, distorted, low quality, text, watermark"
) -> bool:
    """
    Genera una imagen usando Vertex AI con el modelo Imagen 2.

    Args:
        project_id (str): El ID de tu proyecto de Google Cloud.
        location (str): La ubicación del proyecto (ej: "us-central1").
        prompt (str): El prompt para la imagen.
        output_path (Path): La ruta donde se guardará la imagen generada.
        negative_prompt (str): El prompt negativo.

    Returns:
        bool: True si la imagen se generó y guardó correctamente, False si no.
    """
    try:
        print("🖼️  Inicializando Vertex AI...")

        # --- Autenticación con Cuenta de Servicio (Método Robusto) ---
        # Construye la ruta al archivo de credenciales.
        # Asume que el script se ejecuta desde la raíz del proyecto.
        credentials_path = os.path.join(os.getcwd(), 'config', 'credentials', 'vertex_ai_credentials.json')

        if not os.path.exists(credentials_path):
            print(f"❌ Error Crítico: No se encontró el archivo de credenciales en {credentials_path}")
            print("   Asegúrate de haber creado una cuenta de servicio y guardado la llave JSON en esa ruta.")
            return False

        # Carga las credenciales desde el archivo.
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        
        # Inicializa Vertex AI usando las credenciales explícitas.
        vertexai.init(project=project_id, location=location, credentials=credentials)
        # --- Fin del bloque de autenticación ---

        print(f"   - Conectado al proyecto '{project_id}' en '{location}' usando cuenta de servicio.")
        
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        print("   - Modelo 'imagegeneration@006' cargado (versión más reciente).")
        print(f"   - Generando imagen con prompt: '{prompt[:60]}...'")

        # Generar la imagen
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            negative_prompt=negative_prompt,
            # Parámetros para formato de Reel/Short
            aspect_ratio="9:16", 
            # Puedes añadir más parámetros aquí si es necesario
        )

        # Verificación robusta para manejar respuestas vacías (filtros de seguridad)
        if images and len(images) > 0:
            # Guardar la imagen en el archivo de salida
            output_path.parent.mkdir(parents=True, exist_ok=True)
            images[0].save(location=str(output_path))
            
            print(f"   ✅ Imagen generada y guardada exitosamente en: {output_path}")
            return True
        else:
            print("   ❌ La API no devolvió ninguna imagen (probablemente por filtros de seguridad).")
            return False

    except Exception as e:
        print(f"❌ Error durante la generación con Vertex AI: {e}")
        import traceback
        traceback.print_exc()
        return False

def generar_imagenes_para_historia_vertex(historia_dir: Path, prompts: list[str]) -> bool:
    """
    Genera todas las imágenes para una historia usando Vertex AI.
    Esta es la función orquestadora que se llamará desde el pipeline.
    """
    print(f"\n🤖 Iniciando generación masiva con Vertex AI para: {historia_dir.name}")
    
    PROJECT_ID = "n8n-yt-458902" 
    LOCATION = "us-central1"
    
    total_prompts = len(prompts)
    imagenes_exitosas = 0

    for i, prompt in enumerate(prompts):
        numero_imagen = i + 1
        print(f"\n--- Procesando imagen {numero_imagen}/{total_prompts} ---")
        
        output_path = historia_dir / f"imagen_{numero_imagen}.png"
        
        # Usamos la función de generación individual que ya probamos
        success = generar_imagen_vertex(
            project_id=PROJECT_ID,
            location=LOCATION,
            prompt=prompt,
            output_path=output_path
        )
        
        if success:
            imagenes_exitosas += 1
        else:
            print(f"⚠️ Fallo al generar la imagen {numero_imagen}. Continuando con la siguiente.")
    
    print(f"\n🏁 Proceso de Vertex AI finalizado.")
    print(f"   Imágenes generadas exitosamente: {imagenes_exitosas}/{total_prompts}")

    # Devolvemos True solo si TODAS las imágenes se generaron correctamente
    return imagenes_exitosas == total_prompts

if __name__ == '__main__':
    # --- ZONA DE PRUEBAS - ESTOICISMO ---
    PROJECT_ID = "n8n-yt-458902" 
    LOCATION = "us-central1"

    # 1. PLANTILLA DE CALIDAD
    quality_enhancers = (
        "Cinematic photo, detailed portrait, hyper-realistic, 8k, masterpiece, sharp focus, "
        "dramatic lighting, shot on 70mm film, detailed skin texture, philosophical atmosphere"
    )

    # 2. DESCRIPCIÓN VISUAL DE LA ESCENA
    scene_description = (
        "An old stoic philosopher with a long white beard, dressed in a simple white toga. "
        "He is seated in a marble portico, looking thoughtfully into the distance. "
        "Behind him, ancient columns rise towards a clear sky. "
        "His face shows wisdom, resilience, and profound inner peace. The sunlight is soft and contemplative."
    )
    
    # 3. COMBINACIÓN PARA EL PROMPT FINAL
    test_prompt = f"{quality_enhancers}. {scene_description}"

    # Ruta de salida para la imagen de prueba
    test_output_path = Path("output/test_vertex/test_image_vertex_stoicism_test.png")

    print("\n" + "="*60)
    print("🚀 Iniciando prueba sobre estoicismo con Vertex AI...")
    print("="*60)

    # --- Llamada a la API con parámetros de calidad y cuenta de servicio ---
    try:
        credentials_path = os.path.join(os.getcwd(), 'config', 'credentials', 'vertex_ai_credentials.json')
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"El archivo de credenciales no se encontró en: {credentials_path}")
            
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        print("   - Autenticación con cuenta de servicio exitosa para prueba.")
        
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        images = model.generate_images(
            prompt=test_prompt,
            number_of_images=1,
            negative_prompt="blurry, distorted, low quality, text, watermark, cartoon, anime, drawing, painting, aggressive, violent, modern clothing",
            aspect_ratio="9:16",
            guidance_scale=18,
            seed=321, # Nueva seed para una nueva imagen
            add_watermark=False
        )
        
        if images:
            images[0].save(location=str(test_output_path))
            print(f"✅ Imagen de prueba final guardada en: {test_output_path}")
        else:
            print("❌ No se pudo generar la imagen.")

    except Exception as e:
        print(f"❌ Error durante la prueba de Vertex AI: {e}")
        import traceback
        traceback.print_exc()

    print("\n🏁 Prueba finalizada.") 