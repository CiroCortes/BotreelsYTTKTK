from gradio_client import Client
from pathlib import Path
import shutil
import time

class HuggingFaceClient:
    def __init__(self, space_name="black-forest-labs/FLUX.1-dev"):
        self.space_name = space_name
        self.client = Client(space_name)
    def generar_imagen(self, prompt, output_path, width=864, height=1536):
        start_time = time.time()
        result_path = self.client.predict(
            prompt=prompt,
            seed=0,
            randomize_seed=True,
            width=width,
            height=height,
            guidance_scale=3.5,
            num_inference_steps=28,
            api_name="/infer"
        )
        temp_file_path = result_path[0] if isinstance(result_path, tuple) else result_path
        if isinstance(temp_file_path, str) and Path(temp_file_path).exists():
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(temp_file_path, output_path)
            print(f"🖼️ Imagen guardada exitosamente en: {output_path}")
            print(f"   ⏱️ Tiempo de generación: {time.time() - start_time:.1f} segundos")
            return True
        else:
            print(f"❌ El resultado de la API no es una ruta de archivo válida: {temp_file_path}")
            return False 