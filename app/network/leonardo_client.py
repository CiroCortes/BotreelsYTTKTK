import requests
import time
from PIL import Image
import io
from pathlib import Path
from datetime import datetime, timedelta
import threading

class RateLimiter:
    def __init__(self, max_requests_per_minute=30):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
    def can_make_request(self):
        now = datetime.now()
        with self.lock:
            self.requests = [req_time for req_time in self.requests if now - req_time < timedelta(minutes=1)]
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    def wait_if_needed(self):
        while not self.can_make_request():
            print("   ⏳ Rate limit alcanzado, esperando...")
            time.sleep(2)

class LeonardoClient:
    def __init__(self, api_key_path=None):
        if api_key_path is None:
            api_key_path = Path("config/credentials/leonardo_api_key.txt")
        self.api_key = Path(api_key_path).read_text().strip()
        self.rate_limiter = RateLimiter(max_requests_per_minute=30)
        self.model_id = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3"
        self.style_uuid = "111dc692-d470-4eec-b791-3475abac4c46"
        self.contrast = 3.5
        self.width = 864
        self.height = 1536
        self.ultra = False
        self.enhance_prompt = False
    def generar_imagen(self, prompt, output_path, max_intentos=3):
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json"
        }
        prompt_limpio = prompt.strip()[:1000]
        payload = {
            "modelId": self.model_id,
            "contrast": self.contrast,
            "prompt": prompt_limpio,
            "num_images": 1,
            "width": self.width,
            "height": self.height,
            "ultra": self.ultra,
            "styleUUID": self.style_uuid,
            "enhancePrompt": self.enhance_prompt
        }
        for intento in range(max_intentos):
            try:
                self.rate_limiter.wait_if_needed()
                resp = requests.post("https://cloud.leonardo.ai/api/rest/v1/generations", json=payload, headers=headers, timeout=30)
                if resp.status_code == 400:
                    payload["contrast"] = 2.0
                    payload["ultra"] = False
                    continue
                elif resp.status_code in [401, 403]:
                    return False
                elif resp.status_code == 429:
                    time.sleep(60)
                    continue
                resp.raise_for_status()
                generation_id = resp.json()["sdGenerationJob"]["generationId"]
            except Exception:
                if intento < max_intentos - 1:
                    time.sleep(5)
                    continue
                else:
                    return False
            url_get = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
            max_consultas = 7
            for consulta in range(max_consultas):
                if consulta > 0:
                    time.sleep(40)
                try:
                    self.rate_limiter.wait_if_needed()
                    r = requests.get(url_get, headers=headers, timeout=30)
                    r.raise_for_status()
                    data = r.json()
                    gen = data.get("generations_by_pk")
                    if gen and gen.get("status") == "COMPLETE":
                        for img_info in gen.get("generated_images", []):
                            img_url = img_info.get("url")
                            if img_url:
                                img_data = requests.get(img_url, timeout=30).content
                                img = Image.open(io.BytesIO(img_data))
                                if img.size != (self.width, self.height):
                                    img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                                output_path = Path(output_path)
                                output_path.parent.mkdir(parents=True, exist_ok=True)
                                img.save(output_path, "PNG")
                                print(f"   ✅ Imagen guardada: {output_path.name} ({self.width}x{self.height})")
                                return True
                except Exception:
                    continue
        return False 