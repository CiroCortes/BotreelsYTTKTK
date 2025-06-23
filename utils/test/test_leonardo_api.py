import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto al sys.path
# para que podamos importar módulos de 'utils'
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from utils.generar_imagenes_leonardo import generar_imagen_leonardo_robusto

def main():
    """
    Función principal para probar la generación de imágenes con Leonardo.ai.
    """
    print("🚀 Iniciando prueba de la API de Leonardo.ai...")

    # --- Configuración de la prueba ---
    # Puedes modificar este prompt para tus experimentos
    prompt_de_prueba = "a dramatic and cinematic shot of a majestic lion in the middle of a roman coliseum, epic lighting, hyper-realistic"

    # Directorio de salida para las imágenes de prueba
    output_dir = project_root / "output" / "test_leonardo"
    output_dir.mkdir(exist_ok=True)

    # Nombre del archivo de salida
    output_filename = "test_image_1.png"
    output_path = output_dir / output_filename

    print(f"   📝 Prompt: '{prompt_de_prueba}'")
    print(f"   💾 Ruta de salida: {output_path}")

    # --- Llamada a la función de generación ---
    success = generar_imagen_leonardo_robusto(
        prompt=prompt_de_prueba,
        output_path=output_path,
        max_intentos=2 # Podemos usar menos intentos para pruebas rápidas
    )

    if success:
        print(f"\n✅ ¡Prueba finalizada con éxito! Imagen guardada en: {output_path}")
    else:
        print(f"\n❌ La prueba falló. Revisa los logs de error de la consola.")

if __name__ == "__main__":
    main() 