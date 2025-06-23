import os
from pathlib import Path

# --- CORRECCIÓN DE RUTA DE CACHÉ ---
# Establecer HF_HOME ANTES de importar diffusers para asegurar que se use el directorio correcto.
# Esto asegura que tanto la ejecución directa del script como su importación usen la caché correcta.
if not os.getenv("HF_HOME"):
    os.environ['HF_HOME'] = "C:/stable-diffusion-cache"

import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler, EulerAncestralDiscreteScheduler
from PIL import Image
import time
from datetime import datetime
import random
import cv2
import numpy as np
# from realesrgan import RealESRGANer

# --- CONFIGURACIÓN GLOBAL ---
# Resolución para Reels/TikTok
REEL_WIDTH = 720
REEL_HEIGHT = 1280
REEL_ASPECT_RATIO = "9:16"

# Pasos de inferencia por defecto - AUMENTADOS PARA MÁXIMA CALIDAD
DEFAULT_NUM_INFERENCE_STEPS = 50

# Guidance scale por defecto - AUMENTADO PARA MEJOR ADHERENCIA AL PROMPT
DEFAULT_GUIDANCE_SCALE = 11

# Peso del LoRA por defecto - AJUSTADO PARA REALISMO CINEMATOGRÁFICO
DEFAULT_LORA_SCALE = 0.9

# Prompt negativo por defecto para mejorar la calidad y evitar resultados no deseados
DEFAULT_NEGATIVE_PROMPT = (
    "nsfw, deformed, bad anatomy, disfigured, poorly drawn face, mutation, mutated, "
    "extra limb, ugly, disgusting, poorly drawn hands, missing limb, floating limbs, "
    "disconnected limbs, malformed hands, blurry, ((((mutated hands and fingers)))), "
    "watermark, watermarked, oversaturated, censorship, censored, distorted hands, "
    "amputation, missing hands, obese, doubled face, doubled head, "
    # --- TÉRMINOS REFORZADOS PARA EVITAR IMÁGENES DUPLICADAS ---
    "(two scenes:1.5), (split image:1.5), (stacked image:1.5), (multiple panels:1.5), "
    "(collage:1.4), (grid:1.4), (split screen:1.5), (frame:1.3), (border:1.3), "
    "(two images:1.5), (double image:1.5), (multiple compositions:1.5), (duplicate:1.4)"
)

# --- CONFIGURACIÓN DEL ESCALADOR ---
UPSCALER = None

# def get_upscaler():
#     """Inicializa el escalador RealESRGAN si no está cargado."""
#     global UPSCALER
#     if UPSCALER is None:
#         print("🚀 Inicializando escalador RealESRGAN por primera vez...")
#         # Modelo RealESRGAN_x4plus_anime_6B para un look más estilizado o RealESRGAN_x4plus para realismo
#         UPSCALER = RealESRGANer(
#             scale=4,
#             model_path='weights/RealESRGAN_x4plus.pth', # Asegúrate de que este archivo exista
#             dni_weight=None,
#             model=None,
#             tile=0,
#             tile_pad=10,
#             pre_pad=0,
#             half=True, # Usar half-precision para más velocidad en GPUs compatibles
#             gpu_id=0
#         )
#         print("✅ Escalador cargado.")
#     return UPSCALER

# def upscale_image(input_path, output_path, target_width=1080, target_height=1920):
#     """Escala una imagen a la resolución deseada usando Real-ESRGAN."""
#     try:
#         upscaler = get_upscaler()
#         img = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
#         if img is None:
#             print(f"❌ No se pudo leer la imagen de entrada: {input_path}")
#             return False

#         print(f"📈 Escalando imagen de {img.shape[1]}x{img.shape[0]} a {target_width}x{target_height}...")
#         start_time = time.time()

#         # Escalar la imagen (output es una imagen de numpy)
#         output, _ = upscaler.enhance(img, outscale=4) # El modelo escala por 4 por defecto

#         # Redimensionar a las dimensiones exactas de TikTok/Reels
#         output = cv2.resize(output, (target_width, target_height), interpolation=cv2.INTER_AREA)

#         # Guardar la imagen escalada
#         cv2.imwrite(str(output_path), output)

#         tiempo_total = time.time() - start_time
#         print(f"✅ Imagen escalada y guardada en: {output_path.name}")
#         print(f"   Tiempo de escalado: {tiempo_total:.1f}s")
#         return True
#     except Exception as e:
#         print(f"❌ Error durante el escalado: {e}")
#         # Comprobar si el error es por falta de los pesos del modelo
#         if "weights/RealESRGAN_x4plus.pth" in str(e):
#             print("💡 ERROR CRÍTICO: No se encontraron los pesos del modelo RealESRGAN.")
#             print("   Por favor, descarga 'RealESRGAN_x4plus.pth' y colócalo en una carpeta 'weights' en la raíz del proyecto.")
#             print("   Link de descarga: https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth")
#         return False

# Nombre del modelo principal y LoRA por defecto
CACHE_DIR = Path(os.getenv("HF_HOME")) # Ahora leerá el valor correcto
DEFAULT_MODEL = "C:/stable-diffusion-cache/dreamshaper_8.safetensors"
DEFAULT_LORA_NAME = "Biblical"  # Puedes cambiarlo a "Realistic" u otro si lo deseas

class StableDiffusionGenerator:
    def __init__(self, model_name=DEFAULT_MODEL, lora_name=None):
        """
        Inicializa el generador de Stable Diffusion local
        
        Args:
            model_name (str): Nombre del modelo a usar
            lora_name (str, optional): Nombre del LoRA a usar (sin extensión). Si es None, no se carga ningún LoRA.
        """
        self.model_name = model_name
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.lora_loaded = False
        self.lora_name = lora_name
        
        print(f"🖥️ Dispositivo detectado: {self.device}")
        if self.device == "cpu":
            print("⚠️ Usando CPU - La generación será más lenta")
        else:
            print(f"✅ GPU detectada: {torch.cuda.get_device_name()}")
        
        self._load_model()
    
    def _load_model(self):
        """Carga el modelo de Stable Diffusion"""
        try:
            print(f"📥 Cargando modelo: {self.model_name}")
            print(f"   Desde caché: {CACHE_DIR}")
            
            # Forzar float32 para máxima estabilidad en todas las GPUs,
            # previniendo el error de valores 'NaN' que resulta en imágenes negras.
            dtype = torch.float32

            # Usar 'from_single_file' para cargar checkpoints locales (.safetensors)
            # y 'from_pretrained' para repositorios de Hugging Face.
            if Path(self.model_name).is_file() and self.model_name.endswith(".safetensors"):
                print("   Detectado archivo de checkpoint local (.safetensors). Usando 'from_single_file'.")
                self.pipeline = StableDiffusionPipeline.from_single_file(
                    self.model_name,
                    torch_dtype=dtype,
                    use_safetensors=True,
                    safety_checker=None
                )
            else:
                print("   Detectado repo ID de Hugging Face. Usando 'from_pretrained'.")
                self.pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_name,
                    torch_dtype=dtype,
                    use_safetensors=True,
                    cache_dir=str(CACHE_DIR),
                    safety_checker=None
                )
            
            # Optimizar para velocidad y calidad
            self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipeline.scheduler.config
            )
            
            # --- MEJORA CLAVE: Cambiar el scheduler para mejor coherencia ---
            self.pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipeline.scheduler.config)
            
            # --- CORRECCIÓN CRÍTICA: GESTIÓN DE MEMORIA ---
            # Elegir entre offload (ahorro de memoria) o mover todo a la GPU (rendimiento).
            # No se deben usar ambos a la vez.
            if self.device == "cuda" and torch.cuda.get_device_properties(0).total_memory < 9 * 1024**3:
                print("   📉 Detectada VRAM < 9GB. Activando offload a CPU para ahorrar memoria...")
                # offload secuencial es más lento pero consume menos VRAM.
                # a cambio de un poco de velocidad. Es la mejor opción para 4GB.
                self.pipeline.enable_sequential_cpu_offload()
                print("   ✅ Offload a CPU activado. El modelo usará GPU y CPU.")
            else:
                self.pipeline.to(self.device)
                print("   ✅ Pipeline movido completamente a la GPU.")

            # --- Cargar el LoRA opcionalmente ---
            if self.lora_name:
                try:
                    # --- CORRECCIÓN: Usar la ruta base del modelo principal para encontrar la carpeta loras ---
                    model_path = Path(DEFAULT_MODEL)
                    lora_dir = model_path.parent / "loras"
                    lora_path = lora_dir / f"{self.lora_name}.safetensors"

                    if lora_path.exists():
                        print(f"✅ LoRA encontrado en: {lora_path}")
                        self.pipeline.load_lora_weights(lora_path)
                        print(f"✅ LoRA '{self.lora_name}' cargado exitosamente.")
                        self.lora_loaded = True
                    else:
                        print(f"⚠️ No se encontró el LoRA '{self.lora_name}' en la ruta esperada: {lora_path}")
                        print(f"   Para usarlo, asegúrate de que exista la carpeta '{lora_dir}' y que el archivo se llame '{self.lora_name}.safetensors' dentro de ella.")
                        self.lora_loaded = False
                except Exception as lora_error:
                    print(f"❌ Error al cargar el LoRA '{self.lora_name}': {lora_error}")
                    self.lora_loaded = False
            else:
                print("ℹ️ No se especificó ningún LoRA. Usando solo el modelo base.")

            print("✅ Modelo cargado exitosamente")
            
        except Exception as e:
            print(f"❌ Error al cargar el modelo: {e}")
            print("💡 Asegúrate de haber ejecutado 'python install_stable_diffusion.py' primero.")
    
    def _install_dependencies(self):
        """DEPRECATED: La instalación ahora se gestiona en install_stable_diffusion.py"""
        print("Esta función está obsoleta. Ejecuta 'python install_stable_diffusion.py' para instalar.")
    
    def generar_imagen(self, prompt, output_path, 
                      negative_prompt=DEFAULT_NEGATIVE_PROMPT, 
                      width=REEL_WIDTH, height=REEL_HEIGHT, num_inference_steps=DEFAULT_NUM_INFERENCE_STEPS, 
                      guidance_scale=DEFAULT_GUIDANCE_SCALE, seed=None):
        """
        Genera una imagen con Stable Diffusion
        
        Args:
            prompt (str): Descripción de la imagen
            output_path (Path): Ruta donde guardar la imagen
            negative_prompt (str): Lo que NO queremos en la imagen
            width (int): Ancho de la imagen
            height (int): Alto de la imagen
            num_inference_steps (int): Pasos de inferencia (más = mejor calidad)
            guidance_scale (float): Escala de guía (más = más fiel al prompt)
            seed (int): Semilla para reproducibilidad
        
        Returns:
            bool: True si se generó exitosamente
        """
        if not self.pipeline:
            print("❌ Modelo no cargado. No se puede generar la imagen.")
            return False
        
        try:
            print(f"🎨 Generando imagen: {prompt[:50]}...")
            print(f"   Dimensiones: {width}x{height}")
            print(f"   Pasos: {num_inference_steps}")
            print(f"   Guía: {guidance_scale}")
            
            # Generador para reproducibilidad
            generator = None
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
                print(f"   Semilla: {seed}")
            
            # Generar imagen
            start_time = time.time()
            
            image = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator
            ).images[0]
            
            # Guardar imagen
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG")
            
            tiempo_total = time.time() - start_time
            print(f"✅ Imagen generada: {output_path.name}")
            print(f"   Tiempo: {tiempo_total:.1f}s")
            print(f"   Tamaño: {width}x{height}")
            print(f"   💰 Costo: $0 (gratis)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generando imagen: {e}")
            return False
    
    def generar_imagenes_para_historia(self, historia_dir, prompts, 
                                     negative_prompt=DEFAULT_NEGATIVE_PROMPT, 
                                     width=REEL_WIDTH, height=REEL_HEIGHT, num_inference_steps=DEFAULT_NUM_INFERENCE_STEPS):
        """
        Genera múltiples imágenes para una historia
        
        Args:
            historia_dir (str): Directorio de la historia
            prompts (list): Lista de prompts
            negative_prompt (str): Prompt negativo común
            width (int): Ancho de las imágenes
            height (int): Alto de las imágenes
        
        Returns:
            list: Lista de rutas de imágenes generadas
        """
        historia_path = Path(historia_dir)
        imagenes_generadas = []
        
        print(f"🎬 Generando {len(prompts)} imágenes para: {historia_path.name}")
        print(f"💰 Costo total: $0 (completamente gratis)")
        
        for i, prompt in enumerate(prompts, 1):
            # Comprobar si la imagen ya existe
            output_path = historia_path / f"imagen_{i}.png"
            if output_path.exists():
                print(f"✅ Imagen {i}/{len(prompts)} ya existe. Saltando.")
                imagenes_generadas.append(output_path)
                continue

            print(f"\n📸 Imagen {i}/{len(prompts)}")
            
            # Crear nombre de archivo
            imagen_path = historia_path / f"imagen_{i}.png"
            
            # Generar imagen
            success = self.generar_imagen(
                prompt=prompt,
                output_path=imagen_path,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps
            )
            
            if success:
                imagenes_generadas.append(imagen_path)
                print(f"   ✅ Imagen {i} generada exitosamente")
            else:
                print(f"   ❌ Fallo en imagen {i}")
            
            # Pausa entre imágenes
            if i < len(prompts):
                print(f"   ⏳ Pausa de 2 segundos...")
                time.sleep(2)
        
        print(f"\n🎯 Resumen:")
        print(f"   ✅ Imágenes generadas: {len(imagenes_generadas)}/{len(prompts)}")
        print(f"   💰 Costo total: $0")
        print(f"   💰 Ahorro vs Leonardo.ai: ${len(imagenes_generadas) * 0.15:.2f}")
        
        return imagenes_generadas

    def generar_imagenes(self, prompts, historia_path):
        if not self.pipeline:
            print("❌ El pipeline del modelo no está cargado. No se pueden generar imágenes.")
            return []

        print("⏳ Generando imágenes con Stable Diffusion...")
        imagenes_generadas = []
        
        # Parámetros de generación de alta calidad
        width = REEL_WIDTH
        height = REEL_HEIGHT
        num_inference_steps = DEFAULT_NUM_INFERENCE_STEPS # Más pasos para mayor detalle
        guidance_scale = DEFAULT_GUIDANCE_SCALE     # Mayor guía del prompt
        lora_scale = DEFAULT_LORA_SCALE         # Intensidad del LoRA
        
        for i, prompt in enumerate(prompts):
            print(f"\n--- Generando imagen {i+1}/{len(prompts)} ---")
            
            output_path = historia_path / f"imagen_{i+1}.png"
            
            success = self.generate_image(
                prompt=prompt,
                output_path=output_path,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                lora_scale=lora_scale
            )
            
            if success:
                imagenes_generadas.append(output_path)
            else:
                print(f"⚠️ Falló la generación de la imagen {i+1}. Saltando.")


        print("\n✅ Proceso de generación de imágenes finalizado.")
        return imagenes_generadas

    def generate_image(self, prompt, output_path, width, height, num_inference_steps, guidance_scale, lora_scale=DEFAULT_LORA_SCALE):
        """
        Genera una única imagen con los parámetros dados y opcionalmente aplica un LoRA.
        """
        if not self.pipeline:
            print("❌ El modelo no está cargado. No se puede generar la imagen.")
            return False

        print(f"⏳ Generando imagen con Stable Diffusion para: \"{prompt[:80]}...\"")
        print(f"   Configuración: {width}x{height}, Pasos: {num_inference_steps}, Guía: {guidance_scale}, Fuerza LoRA: {lora_scale if self.lora_loaded else 'N/A'}")

        # --- MEJORA CLAVE: Reforzar el prompt para una única escena y composición vertical ---
        reinforced_prompt = (
            f"masterpiece, best quality, ultra-detailed, (vertical composition:1.4), "
            f"(one single cohesive scene:1.4), {REEL_ASPECT_RATIO} aspect ratio, {prompt}"
        )

        # Usar un generador de semillas aleatorio para obtener resultados variados
        generator = torch.Generator(device="cuda").manual_seed(random.randint(0, 2**32 - 1))
        
        kwargs = {}
        if self.lora_loaded:
            kwargs["cross_attention_kwargs"] = {"scale": lora_scale}
            print(f"   - Aplicando LoRA '{self.lora_name}' con peso: {lora_scale}")

        start_time = time.time()
        # Generar la imagen
        image = self.pipeline(
            prompt=reinforced_prompt,
            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
            **kwargs
        ).images[0]
        
        end_time = time.time()
        
        # Guardar imagen
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "PNG")
        
        tiempo_total = end_time - start_time
        print(f"✅ Imagen generada: {output_path.name}")
        print(f"   Tiempo: {tiempo_total:.1f}s")
        print(f"   Tamaño: {width}x{height}")
        print(f"   💰 Costo: $0 (gratis)")
        
        return True

# Instancia global
sd_generator = None

def get_sd_generator(lora_name=DEFAULT_LORA_NAME):
    """Obtiene la instancia global del generador, permitiendo elegir el LoRA"""
    global sd_generator
    if sd_generator is None or sd_generator.lora_name != lora_name:
        print(f"🚀 Inicializando generador de Stable Diffusion con LoRA '{lora_name}'...")
        sd_generator = StableDiffusionGenerator(model_name=DEFAULT_MODEL, lora_name=lora_name)
    return sd_generator

def generar_imagen_sd_simple(prompt, output_path, lora_name=DEFAULT_LORA_NAME):
    """Función simple para generar una imagen con elección de LoRA"""
    generator = get_sd_generator(lora_name=lora_name)
    return generator.generar_imagen(prompt, Path(output_path))

if __name__ == "__main__":
    # Test del generador
    print("🧪 Probando Stable Diffusion local...")
    # Buscar todos los LoRA disponibles en la carpeta 'loras'
    model_path = Path(DEFAULT_MODEL)
    lora_dir = model_path.parent / "loras"
    lora_files = sorted([f for f in lora_dir.glob("*.safetensors")])
    lora_names = [f.stem for f in lora_files]
    # Asegurarse de que el LoRA por defecto esté primero
    if DEFAULT_LORA_NAME in lora_names:
        lora_names.remove(DEFAULT_LORA_NAME)
        lora_names.insert(0, DEFAULT_LORA_NAME)
    print("\nModelos LoRA disponibles:")
    for idx, lora in enumerate(lora_names, 1):
        print(f"  {idx}. {lora}")
    print(f"  [Enter] para usar el LoRA por defecto: {DEFAULT_LORA_NAME}")
    opcion = input("\nElige el número del LoRA a usar: ").strip()
    if opcion == "":
        lora_a_probar = DEFAULT_LORA_NAME
    else:
        try:
            idx = int(opcion) - 1
            if 0 <= idx < len(lora_names):
                lora_a_probar = lora_names[idx]
            else:
                print("Opción inválida. Usando el LoRA por defecto.")
                lora_a_probar = DEFAULT_LORA_NAME
        except Exception:
            print("Entrada inválida. Usando el LoRA por defecto.")
            lora_a_probar = DEFAULT_LORA_NAME
    print(f"\n🔄 Usando LoRA: {lora_a_probar}")
    test_prompt = "A cinematic, ultra-realistic, epic biblical scene with dramatic lighting and apocalyptic atmosphere, 9:16 aspect ratio. King Darius, a cruel and imposing figure in regal Persian attire, watches from a high vantage point, his face a mask of jealous fury, as Daniel, a righteous and calm figure in simple linen robes, is cast into a deep, stone pit teeming with ferocious, snarling lions. The lions' eyes gleam with predatory hunger in the flickering torchlight. The action centers on Daniel's unwavering faith amidst the looming threat, his hands raised in prayer. The mood is one of intense suspense and dread, juxtaposed with Daniel's serene acceptance. The composition uses a high-angle shot showcasing Darius's power and a low-angle shot emphasizing the lions' ferocity, then switches to a close-up of Daniel's face reflecting inner peace. The lighting is primarily dramatic chiaroscuro, with pools of harsh torchlight illuminating the pit and the king, casting long, menacing shadows. Atmospheric effects include swirling dust motes in the air and a palpable sense of foreboding, enhancing the apocalyptic feel. The background features the imposing architecture of a Persian palace, silhouetted against a stormy, blood-red sky."
    # --- CORRECCIÓN DE RUTA DE SALIDA ---
    project_root = Path(__file__).parent.parent
    generator = get_sd_generator(lora_name=lora_a_probar)
    if generator and generator.pipeline:
        test_output = project_root / "output" / "test_sd" / f"test_imagen_sd_{lora_a_probar}.png"
        test_output.parent.mkdir(parents=True, exist_ok=True)
        success = generator.generate_image(test_prompt, test_output, REEL_WIDTH, REEL_HEIGHT, DEFAULT_NUM_INFERENCE_STEPS, DEFAULT_GUIDANCE_SCALE, DEFAULT_LORA_SCALE)
        if success:
            print(f"✅ Test exitoso con LoRA '{lora_a_probar}'. Imagen guardada en: {test_output.resolve()}")
        else:
            print(f"❌ Test falló con LoRA '{lora_a_probar}'")
    else:
        print(f"❌ No se pudo inicializar el generador con LoRA '{lora_a_probar}'. Finalizando prueba.") 