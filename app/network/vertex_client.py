import os
from pathlib import Path
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.oauth2 import service_account

class VertexClient:
    def __init__(self, project_id, location, creds_path=None):
        if creds_path is None:
            creds_path = os.path.join(os.getcwd(), 'config', 'credentials', 'vertex_ai_credentials.json')
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"No se encontró el archivo de credenciales en {creds_path}")
        self.credentials = service_account.Credentials.from_service_account_file(creds_path)
        self.project_id = project_id
        self.location = location
        vertexai.init(project=project_id, location=location, credentials=self.credentials)
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
    def generar_imagen(self, prompt, output_path, negative_prompt="blurry, distorted, low quality, text, watermark"):
        images = self.model.generate_images(
            prompt=prompt,
            number_of_images=1,
            negative_prompt=negative_prompt,
            aspect_ratio="9:16"
        )
        if images and len(images) > 0:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            images[0].save(location=str(output_path))
            print(f"   ✅ Imagen generada y guardada exitosamente en: {output_path}")
            return True
        else:
            print("   ❌ La API no devolvió ninguna imagen (probablemente por filtros de seguridad).")
            return False 