from gradio_client import Client
import shutil
from pathlib import Path
import queue
import time

def generar_imagen_flux(prompt: str, output_path: Path):
    """
    Genera una imagen usando el modelo FLUX.1 en Hugging Face.

    Args:
        prompt (str): El prompt para la imagen.
        output_path (Path): La ruta donde guardar la imagen final.

    Returns:
        bool: True si la imagen se generó y guardó correctamente, False en caso contrario.
    """
    print(f"🔌 Conectando al espacio de Hugging Face: black-forest-labs/FLUX.1-dev")
    start_time = time.time()
    try:
        # Inicializar el cliente para la API de Gradio
        client = Client("black-forest-labs/FLUX.1-dev")
        
        # Parámetros para la generación, optimizados para shorts (formato vertical 9:16)
        width = 864 
        height = 1536

        print(f"🚀 Enviando prompt a FLUX.1: '{prompt[:70]}...'")
        result_path = client.predict(
            prompt=prompt,
            seed=0,
            randomize_seed=True,
            width=width,
            height=height,
            guidance_scale=3.5,
            num_inference_steps=28,
            api_name="/infer"
        )
        
        print(f"✅ Predicción recibida. Archivo temporal en: {result_path}")

        # La API de Gradio devuelve una tupla (ruta_archivo, seed), extraemos la ruta
        temp_file_path = result_path[0] if isinstance(result_path, tuple) else result_path

        # El resultado de la API es la ruta a un archivo temporal.
        # Debemos moverlo a nuestro directorio de proyecto.
        if isinstance(temp_file_path, str) and Path(temp_file_path).exists():
            # Asegurarse de que el directorio de destino exista
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Mover el archivo generado a la ruta de salida deseada
            shutil.move(temp_file_path, output_path)
            
            end_time = time.time()
            print(f"🖼️ Imagen guardada exitosamente en: {output_path}")
            print(f"   ⏱️ Tiempo de generación: {end_time - start_time:.1f} segundos")
            return True
        else:
            print(f"❌ El resultado de la API no es una ruta de archivo válida: {temp_file_path}")
            return False

    except Exception as e:
        print(f"❌ Error durante la generación de imagen con FLUX.1: {e}")
        return False

def generar_imagenes_para_historia_flux(historia_dir: Path, prompts: list[str]) -> bool:
    """
    Orquesta la generación de todas las imágenes para una historia usando FLUX.1.
    Comprueba si las imágenes ya existen antes de generarlas.

    Args:
        historia_dir (Path): Directorio de la historia.
        prompts (list[str]): Lista de prompts a generar.

    Returns:
        bool: True si todas las imágenes se generaron o ya existían, False si hubo errores.
    """
    print(f"\n--- Iniciando generación con Hugging Face (FLUX.1) para: {historia_dir.name} ---")
    total_prompts = len(prompts)
    imagenes_generadas = 0
    imagenes_existentes = 0
    errores = 0

    for i, prompt in enumerate(prompts, 1):
        output_path = historia_dir / f"imagen_{i}.png"
        print(f"\n[{i}/{total_prompts}] Procesando prompt...")

        if output_path.exists():
            print(f"   ✅ La imagen '{output_path.name}' ya existe. Saltando.")
            imagenes_existentes += 1
            continue

        success = generar_imagen_flux(prompt, output_path)
        
        if success:
            imagenes_generadas += 1
        else:
            errores += 1
            print(f"   ❌ Error al generar la imagen para el prompt {i}. Se continuará con el siguiente.")

    print(f"\n--- Resumen de generación para '{historia_dir.name}' ---")
    print(f"   Imágenes generadas ahora: {imagenes_generadas}")
    print(f"   Imágenes que ya existían: {imagenes_existentes}")
    print(f"   Errores de generación: {errores}")

    if errores > 0:
        print("   ⚠️ Hubo errores durante el proceso. Es posible que el video no se pueda crear.")
        return False
    
    print("   ✅ Todas las imágenes necesarias están listas.")
    return True

if __name__ == '__main__':
    # Script de prueba para verificar que el generador funciona de forma independiente.
    print("--- INICIANDO PRUEBA DEL GENERADOR HUGGING FACE (FLUX.1) ---")
    
    # Un prompt de ejemplo, similar a los que genera el bot
    test_prompt = "A cinematic, ultra-realistic, epic biblical scene of a glowing angel descending from the heavens, dramatic lighting and apocalyptic atmosphere, 9:16 aspect ratio."
    
    # Crear un directorio de prueba para la salida
    test_output_dir = Path("output/test_flux")
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    test_output_path = test_output_dir / "test_image_flux.png"

    print(f"\nGenerando imagen de prueba con el prompt:")
    print(f"'{test_prompt}'")
    
    # Ejecutar la función de generación
    success = generar_imagen_flux(test_prompt, test_output_path)

    if success:
        print(f"\n✅ PRUEBA COMPLETADA: La imagen de prueba se guardó en: {test_output_path.resolve()}")
    else:
        print(f"\n❌ PRUEBA FALLIDA: No se pudo generar la imagen.") 