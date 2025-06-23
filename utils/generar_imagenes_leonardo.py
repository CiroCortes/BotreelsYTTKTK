import requests
import time
from PIL import Image
import io
import os
from pathlib import Path
import threading
import queue
from datetime import datetime, timedelta
from typing import Optional

def get_api_key(service_name: str) -> Optional[str]:
    """Carga la API key desde el archivo correspondiente en config/credentials."""
    credential_file = Path(f"config/credentials/{service_name}_api_key.txt")
    if credential_file.exists():
        return credential_file.read_text().strip()
    return None

API_KEY = get_api_key("leonardo")

MODEL_ID = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3"
STYLE_UUID = "111dc692-d470-4eec-b791-3475abac4c46"

# Parámetros fijos para reels/shorts - MODO FAST para reducir costos
CONTRAST = 3.5
WIDTH = 864
HEIGHT = 1536
ULTRA = False  # ❌ DESACTIVADO para reducir costos (11 créditos vs 24)
ENHANCE_PROMPT = False  # ❌ DESACTIVADO para reducir costos

# Rate Limiting para producción
class RateLimiter:
    def __init__(self, max_requests_per_minute=30):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
    
    def can_make_request(self):
        now = datetime.now()
        with self.lock:
            # Limpiar requests antiguos (más de 1 minuto)
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(minutes=1)]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def wait_if_needed(self):
        while not self.can_make_request():
            print("   ⏳ Rate limit alcanzado, esperando...")
            time.sleep(2)

# Instancia global del rate limiter
rate_limiter = RateLimiter(max_requests_per_minute=30)

def generar_imagen_leonardo_robusto(prompt, output_path, max_intentos=3):
    """
    Genera una imagen con Leonardo.ai con validación robusta y fallback.
    Estrategia eficiente: POST → esperar 40 segundos → GET → repetir hasta 7 veces.
    
    💰 MODO FAST ACTIVADO: 11 créditos por imagen (vs 24 en modo Quality/Ultra)
    
    Args:
        prompt (str): El prompt para generar la imagen
        output_path (Path): Ruta donde guardar la imagen
        max_intentos (int): Número máximo de intentos
    
    Returns:
        bool: True si se generó exitosamente, False en caso contrario
    """
    if not API_KEY:
        print(f"   ❌ Error: No se encontró la API key para Leonardo.AI.")
        print(f"      Por favor, crea el archivo 'config/credentials/leonardo_api_key.txt' con tu clave.")
        return False

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {API_KEY}",
        "content-type": "application/json"
    }
    
    start_time = time.time() # Iniciar cronómetro

    # Validar y limpiar el prompt
    prompt_limpio = prompt.strip()
    if len(prompt_limpio) > 1000:  # Limitar longitud del prompt
        prompt_limpio = prompt_limpio[:1000]
        print(f"   ⚠️ Prompt truncado a 1000 caracteres")
    
    payload = {
        "modelId": MODEL_ID,
        "contrast": CONTRAST,
        "prompt": prompt_limpio,
        "num_images": 1,
        "width": WIDTH,
        "height": HEIGHT,
        "ultra": ULTRA,
        "styleUUID": STYLE_UUID,
        "enhancePrompt": ENHANCE_PROMPT
    }
    
    # Validar parámetros antes de enviar
    if not prompt_limpio:
        print(f"   ❌ Error: Prompt vacío")
        return False
    
    if WIDTH <= 0 or HEIGHT <= 0:
        print(f"   ❌ Error: Dimensiones inválidas: {WIDTH}x{HEIGHT}")
        return False
    
    print(f"💰 MODO FAST ACTIVADO - Costo: 11 créditos por imagen (vs 24 en modo Quality)")
    
    for intento in range(max_intentos):
        print(f"🖼️ Generando imagen (Intento {intento + 1}/{max_intentos})...")
        print(f"   Prompt: {prompt_limpio[:50]}...")
        print(f"   Dimensiones: {WIDTH}x{HEIGHT}")
        
        try:
            # Rate limiting antes de la solicitud POST
            rate_limiter.wait_if_needed()
            
            # 1. SOLICITAR generación (POST)
            resp = requests.post("https://cloud.leonardo.ai/api/rest/v1/generations", 
                               json=payload, headers=headers, timeout=30)
            
            # Diagnóstico detallado de errores
            if resp.status_code == 400:
                error_detail = resp.json() if resp.content else "Sin detalles"
                print(f"   ❌ Error 400 - Bad Request:")
                print(f"      Detalles: {error_detail}")
                print(f"      Payload enviado: {payload}")
                # Intentar con parámetros más conservadores
                payload["contrast"] = 2.0  # Reducir contraste
                payload["ultra"] = False   # Desactivar ultra
                print(f"   🔄 Reintentando con parámetros más conservadores...")
                continue
            elif resp.status_code == 401:
                print(f"   ❌ Error 401 - API Key inválida o expirada")
                return False
            elif resp.status_code == 403:
                print(f"   ❌ Error 403 - Sin permisos o límite excedido")
                return False
            elif resp.status_code == 429:
                print(f"   ❌ Error 429 - Rate limit excedido, esperando...")
                time.sleep(60)  # Esperar 1 minuto
                continue
            
            resp.raise_for_status()
            generation_id = resp.json()["sdGenerationJob"]["generationId"]
            print(f"   ✅ Generación iniciada: {generation_id}")
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error en solicitud (Intento {intento + 1}): {e}")
            if intento < max_intentos - 1:
                time.sleep(5)  # Esperar antes del siguiente intento
                continue
            else:
                return False
        
        # 2. ESTRATEGIA EFICIENTE: Esperar 40 segundos, luego consultar
        url_get = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
        max_consultas = 7  # Máximo 7 consultas (4.7 minutos total)
        
        for consulta in range(max_consultas):
            # Esperar 40 segundos antes de consultar
            if consulta > 0:  # No esperar en la primera consulta
                print(f"   ⏳ Esperando 40 segundos antes de consultar...")
                time.sleep(40)  # Esperar 40 segundos (optimizado)
            
            try:
                # Rate limiting antes de cada consulta GET
                rate_limiter.wait_if_needed()
                
                # CONSULTAR estado (GET)
                r = requests.get(url_get, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()
                gen = data.get("generations_by_pk")
                
                if gen and gen.get("status") == "COMPLETE":
                    # ✅ IMAGEN LISTA - Descargar
                    for img_info in gen.get("generated_images", []):
                        img_url = img_info.get("url")
                        if img_url:
                            img_data = requests.get(img_url, timeout=30).content
                            img = Image.open(io.BytesIO(img_data))
                            
                            # Verificar dimensiones
                            if img.size != (WIDTH, HEIGHT):
                                print(f"   ⚠️ Imagen generada con dimensiones incorrectas: {img.size}")
                                img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
                            
                            # Guardar imagen
                            output_path.parent.mkdir(parents=True, exist_ok=True)
                            img.save(output_path, "PNG")
                            
                            end_time = time.time() # Finalizar cronómetro
                            print(f"   ✅ Imagen guardada: {output_path.name} ({WIDTH}x{HEIGHT})")
                            print(f"   ⏱️ Tiempo de generación: {end_time - start_time:.1f} segundos")
                            return True
                    
                    print(f"   ❌ No se encontraron imágenes en la respuesta")
                    break
                    
                elif gen and gen.get("status") == "FAILED":
                    print(f"   ❌ Generación falló: {gen.get('failureReason', 'Razón desconocida')}")
                    break
                    
                elif gen and gen.get("status") in ["PENDING", "IN_PROGRESS"]:
                    tiempo_transcurrido = consulta * 40  # Tiempo en segundos (ajustado)
                    print(f"   ⏳ Imagen en progreso... {tiempo_transcurrido}s transcurridos")
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ Error en consulta {consulta + 1}: {e}")
                continue
        
        if intento < max_intentos - 1:
            print(f"   🔄 Reintentando...")
            time.sleep(10)  # Esperar más tiempo entre intentos
    
    print(f"   ❌ No se pudo generar la imagen después de {max_intentos} intentos (máximo {max_consultas * 40 / 60:.1f} minutos por intento)")
    return False

# Sistema de Cola Asíncrono para Producción
class ImageGenerationQueue:
    def __init__(self, max_workers=5):
        self.queue = queue.Queue()
        self.max_workers = max_workers
        self.workers = []
        self.running = False
    
    def start_workers(self):
        """Inicia los workers para procesar la cola"""
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        print(f"🚀 Iniciados {self.max_workers} workers para generación de imágenes")
    
    def stop_workers(self):
        """Detiene todos los workers"""
        self.running = False
        for worker in self.workers:
            worker.join()
        print("🛑 Workers detenidos")
    
    def add_task(self, prompt, output_path, callback=None):
        """Añade una tarea a la cola"""
        task = {
            'prompt': prompt,
            'output_path': output_path,
            'callback': callback,
            'timestamp': datetime.now()
        }
        self.queue.put(task)
    
    def _worker(self, worker_id):
        """Worker que procesa tareas de la cola"""
        while self.running:
            try:
                task = self.queue.get(timeout=1)
                print(f"   👷 Worker {worker_id} procesando imagen...")
                
                success = generar_imagen_leonardo_robusto(
                    task['prompt'], 
                    task['output_path']
                )
                
                if task['callback']:
                    task['callback'](success, task['output_path'])
                
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"   ❌ Error en worker {worker_id}: {e}")
                if task and task['callback']:
                    task['callback'](False, task['output_path'])
                self.queue.task_done()

# Instancia global de la cola
image_queue = ImageGenerationQueue(max_workers=3)

def generar_imagenes_para_historia_async(historia_dir, prompts, fallback_enabled=True):
    """
    Genera todas las imágenes para una historia usando cola asíncrona.
    Ideal para producción con múltiples clientes.
    
    Args:
        historia_dir (Path): Directorio de la historia
        prompts (list): Lista de prompts
        fallback_enabled (bool): Si usar fallback con última imagen exitosa
    
    Returns:
        bool: True si todas las imágenes se generaron o se usó fallback
    """
    historia_dir = Path(historia_dir)
    resultados = {}
    ultima_imagen_exitosa = None
    
    print(f"\n🖼️ Generando {len(prompts)} imágenes (modo asíncrono)...")
    
    # Iniciar workers si no están corriendo
    if not image_queue.running:
        image_queue.start_workers()
    
    # Función callback para manejar resultados
    def on_image_complete(success, output_path):
        resultados[output_path] = success
        if success:
            print(f"   ✅ Imagen completada: {output_path.name}")
        else:
            print(f"   ❌ Imagen falló: {output_path.name}")
    
    # Añadir todas las tareas a la cola
    for i, prompt in enumerate(prompts, 1):
        img_path = historia_dir / f"imagen_{i}.png"
        
        # Verificar si ya existe
        if img_path.exists():
            print(f"   ✅ Imagen {i} ya existe: {img_path.name}")
            resultados[img_path] = True
            ultima_imagen_exitosa = img_path
            continue
        
        # Añadir a la cola
        image_queue.add_task(prompt, img_path, on_image_complete)
    
    # Esperar a que se completen todas las tareas
    print(f"   ⏳ Esperando que se completen {len(prompts)} imágenes...")
    image_queue.queue.join()
    
    # Procesar resultados y aplicar fallback si es necesario
    for i, prompt in enumerate(prompts, 1):
        img_path = historia_dir / f"imagen_{i}.png"
        
        if not resultados.get(img_path, False):
            print(f"   ❌ Fallo al generar imagen {i}")
            
            # FALLBACK: Usar última imagen exitosa
            if fallback_enabled and ultima_imagen_exitosa:
                print(f"   🔄 Aplicando fallback: duplicando {ultima_imagen_exitosa.name}")
                try:
                    img = Image.open(ultima_imagen_exitosa)
                    img.save(img_path)
                    resultados[img_path] = True
                    print(f"   ✅ Fallback exitoso: {img_path.name}")
                except Exception as e:
                    print(f"   ❌ Error en fallback: {e}")
                    return False
            else:
                print(f"   ❌ No hay imagen de fallback disponible")
                return False
        else:
            ultima_imagen_exitosa = img_path
    
    print(f"\n✅ Proceso completado: {len([r for r in resultados.values() if r])}/{len(prompts)} imágenes generadas")
    return len([r for r in resultados.values() if r]) == len(prompts)

def generar_imagenes_para_historia(historia_dir, prompts, fallback_enabled=True):
    """
    Genera todas las imágenes para una historia con fallback robusto.
    Versión síncrona para desarrollo/testing.
    
    Args:
        historia_dir (Path): Directorio de la historia
        prompts (list): Lista de prompts
        fallback_enabled (bool): Si usar fallback con última imagen exitosa
    
    Returns:
        bool: True si todas las imágenes se generaron o se usó fallback
    """
    historia_dir = Path(historia_dir)
    imagenes_generadas = []
    ultima_imagen_exitosa = None
    
    print(f"\n🖼️ Generando {len(prompts)} imágenes para la historia...")
    
    for i, prompt in enumerate(prompts, 1):
        img_path = historia_dir / f"imagen_{i}.png"
        
        # Verificar si ya existe
        if img_path.exists():
            print(f"   ✅ Imagen {i} ya existe: {img_path.name}")
            imagenes_generadas.append(img_path)
            ultima_imagen_exitosa = img_path
            continue
        
        # Generar nueva imagen
        exito = generar_imagen_leonardo_robusto(prompt, img_path)
        
        if exito:
            imagenes_generadas.append(img_path)
            ultima_imagen_exitosa = img_path
        else:
            print(f"   ❌ Fallo al generar imagen {i}")
            
            # FALLBACK: Usar última imagen exitosa
            if fallback_enabled and ultima_imagen_exitosa:
                print(f"   🔄 Aplicando fallback: duplicando {ultima_imagen_exitosa.name}")
                try:
                    img = Image.open(ultima_imagen_exitosa)
                    img.save(img_path)
                    imagenes_generadas.append(img_path)
                    print(f"   ✅ Fallback exitoso: {img_path.name}")
                except Exception as e:
                    print(f"   ❌ Error en fallback: {e}")
                    return False
            else:
                print(f"   ❌ No hay imagen de fallback disponible")
                return False
    
    print(f"\n✅ Proceso completado: {len(imagenes_generadas)}/{len(prompts)} imágenes generadas")
    return len(imagenes_generadas) == len(prompts)

# Funciones legacy para compatibilidad
def generar_imagen_leonardo(prompt, num_images):
    """Función legacy para compatibilidad con código existente"""
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {API_KEY}",
        "content-type": "application/json"
    }
    print(f"\nGenerando imágenes en {WIDTH}x{HEIGHT} (9:16)...")
    payload = {
        "modelId": MODEL_ID,
        "contrast": CONTRAST,
        "prompt": prompt,
        "num_images": int(num_images),
        "width": WIDTH,
        "height": HEIGHT,
        "ultra": ULTRA,
        "styleUUID": STYLE_UUID,
        "enhancePrompt": ENHANCE_PROMPT
    }
    try:
        resp = requests.post("https://cloud.leonardo.ai/api/rest/v1/generations", json=payload, headers=headers)
        resp.raise_for_status()
        generation_id = resp.json()["sdGenerationJob"]["generationId"]
    except Exception as e:
        print(f"Error al solicitar generación: {e}")
        return None

    # Esperar y obtener la imagen
    url_get = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
    for intento in range(15):
        time.sleep(3)
        try:
            r = requests.get(url_get, headers=headers)
            r.raise_for_status()
            data = r.json()
            gen = data.get("generations_by_pk")
            if gen and gen.get("status") == "COMPLETE":
                images = []
                for idx, img_info in enumerate(gen.get("generated_images", []), 1):
                    img_url = img_info.get("url")
                    if img_url:
                        img_data = requests.get(img_url).content
                        img = Image.open(io.BytesIO(img_data))
                        # Guardar imagen temporalmente
                        filename = f"imagen_generada_{idx}.png"
                        img.save(filename)
                        images.append(img)
                        print(f"✅ Imagen guardada: {filename} ({WIDTH}x{HEIGHT})")
                # Revisar dimensiones
                revisar_dimensiones_imagenes([f"imagen_generada_{i+1}.png" for i in range(len(images))])
                return images
        except Exception as e:
            print(f"Esperando generación... ({intento+1}) {e}")
    print("No se generó la imagen a tiempo.")
    return None

def revisar_dimensiones_imagenes(lista_rutas):
    print("\n--- Revisión de dimensiones de imágenes generadas ---")
    for ruta in lista_rutas:
        if os.path.exists(ruta):
            try:
                img = Image.open(ruta)
                w, h = img.size
                proporcion = w / h
                print(f"{ruta}: {w}x{h} (proporción: {proporcion:.4f})")
            except Exception as e:
                print(f"No se pudo abrir {ruta}: {e}")
        else:
            print(f"No existe el archivo {ruta}") 