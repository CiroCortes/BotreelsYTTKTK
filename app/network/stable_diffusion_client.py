import os
from pathlib import Path
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler, EulerAncestralDiscreteScheduler
from PIL import Image

REEL_WIDTH = 720
REEL_HEIGHT = 1280
DEFAULT_NUM_INFERENCE_STEPS = 50
DEFAULT_GUIDANCE_SCALE = 11
DEFAULT_NEGATIVE_PROMPT = (
    "nsfw, deformed, bad anatomy, disfigured, poorly drawn face, mutation, mutated, "
    "extra limb, ugly, disgusting, poorly drawn hands, missing limb, floating limbs, "
    "disconnected limbs, malformed hands, blurry, ((((mutated hands and fingers)))), "
    "watermark, watermarked, oversaturated, censorship, censored, distorted hands, "
    "amputation, missing hands, obese, doubled face, doubled head, "
    "(two scenes:1.5), (split image:1.5), (stacked image:1.5), (multiple panels:1.5), "
    "(collage:1.4), (grid:1.4), (split screen:1.5), (frame:1.3), (border:1.3), "
    "(two images:1.5), (double image:1.5), (multiple compositions:1.5), (duplicate:1.4)"
)

class StableDiffusionClient:
    def __init__(self, model_name="C:/stable-diffusion-cache/dreamshaper_8.safetensors", lora_name=None):
        self.model_name = model_name
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.lora_loaded = False
        self.lora_name = lora_name
        self._load_model()
    def _load_model(self):
        dtype = torch.float32
        if Path(self.model_name).is_file() and self.model_name.endswith(".safetensors"):
            self.pipeline = StableDiffusionPipeline.from_single_file(
                self.model_name,
                torch_dtype=dtype,
                use_safetensors=True,
                safety_checker=None
            )
        else:
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                use_safetensors=True,
                cache_dir=os.getenv("HF_HOME", "C:/stable-diffusion-cache"),
                safety_checker=None
            )
        self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(self.pipeline.scheduler.config)
        self.pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipeline.scheduler.config)
        if self.device == "cuda" and torch.cuda.get_device_properties(0).total_memory < 9 * 1024**3:
            self.pipeline.enable_sequential_cpu_offload()
        else:
            self.pipeline.to(self.device)
        if self.lora_name:
            model_path = Path(self.model_name)
            lora_dir = model_path.parent / "loras"
            lora_path = lora_dir / f"{self.lora_name}.safetensors"
            if lora_path.exists():
                self.pipeline.load_lora_weights(lora_path)
                self.lora_loaded = True
    def generar_imagen(self, prompt, output_path, negative_prompt=DEFAULT_NEGATIVE_PROMPT, width=REEL_WIDTH, height=REEL_HEIGHT, num_inference_steps=DEFAULT_NUM_INFERENCE_STEPS, guidance_scale=DEFAULT_GUIDANCE_SCALE, seed=None):
        generator = torch.Generator(device=self.device)
        if seed is not None:
            generator.manual_seed(seed)
        image = self.pipeline(
            prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator
        ).images[0]
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        print(f"✅ Imagen generada y guardada en: {output_path}")
        return True 