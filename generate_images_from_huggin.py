import argparse
import os
import time
from pathlib import Path
# Eliminar import requests y json ya que usaremos gradio_client
# import requests
# import json
from PIL import Image
import io
import base64
import gradio as gr
from gradio_client import Client # Importar Gradio Client

# Eliminar la función generar_imagen existente basada en requests
# def generar_imagen(prompt, api_url, max_intentos=3, tiempo_espera=50):
#    ...

# Nueva función para generar imagen usando gradio_client con la nueva API
def generar_imagen_con_client(prompt: str, negative_prompt: str, num_inference_steps: float, guidance_scale: float, width: float, height: float, num_samples: float) -> list[Image.Image] | None:
    """Genera imágenes usando gradio_client y la nueva API de Hugging Face"""
    client = Client("https://armen425221356-unfilteredai-nsfw-gen-v2-self-parms.hf.space/") # Usar la URL base del nuevo Space
    
    try:
        print(f"\n🖼️ Generando imágenes para prompt: {prompt}")
        print(f"📝 Negative Prompt: {negative_prompt}")
        print(f"⚙️ Configuración: steps={num_inference_steps}, scale={guidance_scale}, size={width}x{height}, samples={num_samples}")

        # Llamar al endpoint específico /predict con los nuevos parámetros
        result = client.predict(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            width=width,
            height=height,
            num_samples=num_samples,
            api_name="/predict" # Usar el api_name especificado en la documentación
        )
        
        # La documentación indica que el resultado es List[Dict(image: filepath, caption: str | None)]
        if isinstance(result, list) and all(isinstance(item, dict) and 'image' in item and 'filepath' in item['image'] for item in result):
            print(f"✅ API retornó una lista de {len(result)} imágenes.")
            
            generated_images = []
            for i, item in enumerate(result):
                try:
                    # La key 'image' en el dict de resultado tiene la estructura { 'filepath': '...', ... }
                    image_filepath = item['image']['filepath']
                    print(f"  📥 Cargando imagen {i+1} desde: {image_filepath}")
                    img = Image.open(image_filepath)
                    generated_images.append(img)
                except Exception as img_e:
                    print(f"  ❌ Error al cargar la imagen {i+1} desde {item.get('image', {}).get('filepath')}: {str(img_e)}")
                    # Continuar con las otras imágenes aunque una falle
                    continue
                    
            if generated_images:
                print(f"✅ Cargadas {len(generated_images)} imágenes exitosamente.")
                return generated_images
            else:
                print("❌ No se pudieron cargar imágenes válidas de la respuesta de la API.")
                return None
                
        else:
            print(f"❌ Formato de respuesta de la API inesperado: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Error al usar gradio_client para generar imagen: {str(e)}")
        return None

# Modificar la función para la interfaz de Gradio
# Ahora acepta múltiples entradas para los parámetros de la API
def generar_imagen_gradio(prompt, negative_prompt, num_inference_steps, guidance_scale, width, height, num_samples):
    # Llamar a la nueva función de generación de imagen con todos los parámetros
    return generar_imagen_con_client(prompt, negative_prompt, num_inference_steps, guidance_scale, width, height, num_samples)

# Modificar el bloque if __name__ == "__main__": para configurar la interfaz de Gradio
if __name__ == "__main__":
    print("🚀 Lanzando interfaz de Gradio para probar la generación de imágenes...")
    
    # Configurar y lanzar la interfaz de Gradio con las entradas y salida de la nueva API
    iface = gr.Interface(
        fn=generar_imagen_gradio, 
        inputs=[
            gr.Textbox(label="Prompt", value="a realistic photo of pikachu"), # Prompt de prueba
            gr.Textbox(label="Negative Prompt", value="(low quality, worst quality:1.2), very displeasing, 3d, watermark, signature, ugly, poorly drawn, (deformed | distorted | disfigured:1.3), bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, mutated hands and fingers:1.4, disconnected limbs, blurry, amputation."), # Valor por defecto de la doc
            gr.Slider(minimum=1, maximum=100, value=60, label="Number inference steps"), # Valor por defecto de la doc
            gr.Slider(minimum=1, maximum=20, value=7, label="Guidance scale"), # Valor por defecto de la doc
            gr.Slider(minimum=256, maximum=2048, step=64, value=1024, label="Width"), # Valor por defecto de la doc
            gr.Slider(minimum=256, maximum=2048, step=64, value=1024, label="Height"), # Valor por defecto de la doc
            gr.Slider(minimum=1, maximum=10, step=1, value=7, label="# images") # Valor por defecto de la doc
        ], 
        outputs=gr.Gallery(label="Imágenes Generadas", type="pil"), # Cambiado a Galería
        title="Generador de Imágenes con Hugging Face (UnfilteredAI)",
        description="Ingresa prompts y parámetros para generar imágenes usando la API UnfilteredAI a través de gradio_client."
    )
    
    # El puerto 7860 es el puerto por defecto de Gradio
    iface.launch()

# Código original (comentado o eliminado según la estrategia)
# if __name__ == "__main__":
#    main() 