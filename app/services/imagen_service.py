from pathlib import Path
from utils.file_utils import sanitizar_titulo_para_directorio
from app.models.imagen import Imagen
from app.network.leonardo_client import LeonardoClient
from app.network.vertex_client import VertexClient
from app.network.huggingface_client import HuggingFaceClient
from app.network.stable_diffusion_client import StableDiffusionClient

class ImagenService:
    """
    Servicio para la generación y validación de imágenes a partir de prompts.
    Cada método es autocontenible y maneja sus propios errores.
    """
    def procesar_imagenes_pendientes(self, historias: list[str], prompts_por_historia: dict, modo_imagenes: str = "stable_diffusion"):
        """Procesa todas las imágenes pendientes para una lista de historias y sus prompts."""
        for titulo in historias:
            print(f"\n[NODO IMAGEN] Procesando imágenes para: {titulo}")
            prompts = prompts_por_historia.get(titulo, [])
            if self.validar_imagenes(titulo, prompts):
                print("   ✅ Todas las imágenes ya existen y son válidas.")
                continue
            try:
                imagenes = self.generar_imagenes_para_historia(titulo, prompts, modo_imagenes)
                if self.validar_imagenes(titulo, prompts):
                    print("   ✅ Imágenes generadas correctamente.")
                else:
                    print("   ❌ Error: No se pudo validar la generación de imágenes para:", titulo)
            except Exception as e:
                print(f"   ❌ Error generando imágenes para '{titulo}': {e}")

    def generar_imagenes_para_historia(self, titulo: str, prompts: list[str], modo_imagenes: str = "stable_diffusion") -> list:
        """Genera todas las imágenes para una historia dada y una lista de prompts."""
        titulo_limpio = sanitizar_titulo_para_directorio(titulo)
        historia_dir = Path("historias") / titulo_limpio
        historia_dir.mkdir(parents=True, exist_ok=True)
        if not prompts:
            print("   ⚠️ No hay prompts para esta historia. Saltando generación de imágenes.")
            return []
        print(f"   Generando {len(prompts)} imágenes en modo: {modo_imagenes}")
        imagenes = []
        if modo_imagenes == "leonardo":
            cliente = LeonardoClient()
            for idx, prompt in enumerate(prompts, 1):
                output_path = historia_dir / f"imagen_{idx}.png"
                if output_path.exists() and output_path.stat().st_size > 0:
                    print(f"      ✅ Imagen {idx} ya existe: {output_path.name}")
                    imagenes.append(Imagen.from_path(output_path))
                    continue
                exito = cliente.generar_imagen(prompt, output_path)
                if exito:
                    imagenes.append(Imagen.from_path(output_path))
        elif modo_imagenes == "vertex":
            cliente = VertexClient(project_id="n8n-yt-458902", location="us-central1")
            for idx, prompt in enumerate(prompts, 1):
                output_path = historia_dir / f"imagen_{idx}.png"
                if output_path.exists() and output_path.stat().st_size > 0:
                    print(f"      ✅ Imagen {idx} ya existe: {output_path.name}")
                    imagenes.append(Imagen.from_path(output_path))
                    continue
                exito = cliente.generar_imagen(prompt, output_path)
                if exito:
                    imagenes.append(Imagen.from_path(output_path))
        elif modo_imagenes == "huggingface":
            cliente = HuggingFaceClient()
            for idx, prompt in enumerate(prompts, 1):
                output_path = historia_dir / f"imagen_{idx}.png"
                if output_path.exists() and output_path.stat().st_size > 0:
                    print(f"      ✅ Imagen {idx} ya existe: {output_path.name}")
                    imagenes.append(Imagen.from_path(output_path))
                    continue
                exito = cliente.generar_imagen(prompt, output_path)
                if exito:
                    imagenes.append(Imagen.from_path(output_path))
        elif modo_imagenes == "stable_diffusion":
            cliente = StableDiffusionClient()
            for idx, prompt in enumerate(prompts, 1):
                output_path = historia_dir / f"imagen_{idx}.png"
                if output_path.exists() and output_path.stat().st_size > 0:
                    print(f"      ✅ Imagen {idx} ya existe: {output_path.name}")
                    imagenes.append(Imagen.from_path(output_path))
                    continue
                exito = cliente.generar_imagen(prompt, output_path)
                if exito:
                    imagenes.append(Imagen.from_path(output_path))
        else:
            print(f"   ❌ Modo de imágenes no soportado: {modo_imagenes}")
        return imagenes

    def validar_imagenes(self, titulo: str, prompts: list[str]) -> bool:
        """Valida si todas las imágenes requeridas existen y son correctas para una historia."""
        titulo_limpio = sanitizar_titulo_para_directorio(titulo)
        historia_dir = Path("historias") / titulo_limpio
        total = len(prompts)
        if total == 0:
            return False
        for idx in range(1, total + 1):
            img_path = historia_dir / f"imagen_{idx}.png"
            if not img_path.exists() or img_path.stat().st_size == 0:
                return False
        return True

    def cargar_imagenes(self, titulo: str, total: int) -> list:
        """Carga las imágenes existentes para una historia y retorna una lista de modelos Imagen."""
        titulo_limpio = sanitizar_titulo_para_directorio(titulo)
        historia_dir = Path("historias") / titulo_limpio
        imagenes = []
        for idx in range(1, total + 1):
            img_path = historia_dir / f"imagen_{idx}.png"
            if img_path.exists() and img_path.stat().st_size > 0:
                imagenes.append(Imagen.from_path(img_path))
        return imagenes 