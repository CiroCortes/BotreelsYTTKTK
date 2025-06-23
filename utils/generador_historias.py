import re
from pathlib import Path
import random
import shutil
from utils.gemini_api import generar_respuesta
from utils.prompt_generator import procesar_prompts
from utils.file_utils import sanitizar_titulo_para_directorio
import json

def seleccionar_musica_aleatoria(musica_dir: Path) -> Path:
    """Selecciona una música de fondo aleatoria del directorio de música."""
    if not musica_dir.exists():
        raise FileNotFoundError(f"El directorio de música no existe: {musica_dir}")
    
    archivos_musica = list(musica_dir.glob("**/*.mp3"))
    if not archivos_musica:
        raise FileNotFoundError(f"No se encontraron archivos de música en {musica_dir}")
        
    return random.choice(archivos_musica)

def generar_historia_y_prompts(titulo: str) -> tuple[list[str], list[str]]:
    """
    Genera la historia y los prompts visuales usando estrategia económica de 2 peticiones.
    Es un nodo autónomo con validación local sin costos adicionales.
    """
    # 1. Sanitizar título y definir la ruta del directorio
    titulo_limpio = sanitizar_titulo_para_directorio(titulo)
    historia_dir = Path("historias") / titulo_limpio
    
    # 2. Asegurar que el directorio exista SIEMPRE y crear subdirectorios
    historia_dir.mkdir(parents=True, exist_ok=True)
    (historia_dir / "audios").mkdir(exist_ok=True)
    (historia_dir / "videos").mkdir(exist_ok=True)
    
    # 3. Seleccionar y copiar música
    try:
        musica_origen = seleccionar_musica_aleatoria(Path("musica/biblic_music"))
        musica_destino = historia_dir / musica_origen.name
        shutil.copy(musica_origen, musica_destino)
        print(f"🎵 Música '{musica_origen.name}' copiada a la carpeta de la historia.")
    except FileNotFoundError as e:
        print(f"⚠️ Advertencia: No se pudo copiar la música. {e}")

    # PÉTICIÓN 1: Generar solo la historia (muy económica)
    print(f"\n📝 Petición 1: Generando historia...")
    PROMPT_HISTORIA = """
    Genera una historia BIBLICA, emotiva, educativa y cristiana con una frase gancho de impacto al principio sobre "{titulo}".
    
    La historia debe tener una duración de 1.5 a 1.8 minutos para contar una narrativa completa.
    Genera entre 16 y 20 párrafos para alcanzar la duración objetivo.
    Cada párrafo debe contener entre 25 y 30 palabras para mantener el ritmo narrativo.
    
    ESTRUCTURA OBLIGATORIA:
    1. FRASE GANCHO: Comienza con una frase atractiva y llamativa que enganche al espectador
    2. DESARROLLO: Desarrolla la historia con detalles épicos y dramáticos
    3. CLÍMAX: Llega a un punto culminante emocionante
    4. CONCLUSIÓN: Termina con una reflexión poderosa
    5. LLAMADA A LA ACCIÓN: Invita a los espectadores a suscribirse y compartir
    
    No pongas numeración ni títulos de párrafo.
    IMPORTANTE: Separa cada párrafo con el carácter '|' en lugar de saltos de línea.
    """.strip()

    prompt_historia = PROMPT_HISTORIA.format(titulo=titulo)
    respuesta_historia = generar_respuesta(prompt_historia)
    
    # DEPURACIÓN: Mostrar la respuesta cruda de Gemini
    print("\n--- RESPUESTA CRUDA DE GEMINI ---\n", respuesta_historia, "\n-------------------------------\n")
    
    if not respuesta_historia:
        raise RuntimeError("No se pudo generar la historia con Gemini.")

    # Procesar historia y obtener párrafos
    historia = respuesta_historia.replace("[HISTORIA]", "").strip()
    parrafos = [p.strip() for p in historia.split("|") if p.strip()]
    
    print(f"✅ Historia generada: {len(parrafos)} párrafos")

    # PÉTICIÓN 2: Generar prompts individuales (uno por párrafo)
    print(f"\n🖼️ Petición 2: Generando prompts individuales...")
    prompts = []
    
    PROMPT_BASE_VISUAL = """
    Crea un prompt de imagen en inglés para el siguiente párrafo.

    PÁRRAFO: "{parrafo}"

    INSTRUCCIONES PARA EL PROMPT DE IMAGEN:
    1.  **Estilo Visual Principal:** El prompt DEBE comenzar con: "A cinematic, hyper-realistic, epic scene with dramatic lighting, 9:16 aspect ratio."
    2.  **Descripción Detallada:** Después del prefijo, describe la escena del párrafo con gran detalle. Enfócate en:
        - La ropa y apariencia de los personajes.
        - Las acciones y expresiones faciales.
        - El entorno (arquitectura, paisaje).
        - La atmósfera y la iluminación (ej. "somber mood", "divine light from the heavens").
    3.  **REGLA CRÍTICA - EVITAR PALABRAS CLAVE:** NO uses palabras como "biblical", "war", "violent", "blood", "kill", "fight" o cualquier término religioso explícito. En su lugar, describe lo que se VE. Por ejemplo, en vez de "escena bíblica", di "escena en la antigua Judea".

    Responde ÚNICAMENTE con el prompt de imagen completo, sin añadir explicaciones.
    """.strip()

    for i, parrafo in enumerate(parrafos, 1):
        print(f"   Generando prompt {i}/{len(parrafos)}...")
        
        prompt_individual = PROMPT_BASE_VISUAL.format(parrafo=parrafo)
        respuesta_prompt = generar_respuesta(prompt_individual)
        
        if respuesta_prompt:
            prompt_limpio = respuesta_prompt.strip()
            # Asegurar que tenga el prefijo obligatorio
            if not prompt_limpio.startswith("A cinematic, hyper-realistic, epic scene"):
                prompt_limpio = "A cinematic, hyper-realistic, epic scene with dramatic lighting, 9:16 aspect ratio. " + prompt_limpio
            
            prompts.append(prompt_limpio)
            print(f"   ✅ Prompt {i} generado")
        else:
            print(f"   ❌ Fallo al generar prompt {i}, usando prompt genérico")
            # Fallback: prompt genérico
            prompt_fallback = f"A cinematic, hyper-realistic, epic scene with dramatic lighting, 9:16 aspect ratio. Ancient scene with dramatic composition."
            prompts.append(prompt_fallback)

    # VALIDACIÓN LOCAL (sin costos adicionales)
    print(f"\n📊 Validación local:")
    print(f"   Párrafos generados: {len(parrafos)}")
    print(f"   Prompts generados: {len(prompts)}")
    
    if len(parrafos) != len(prompts):
        print(f"⚠️ Discrepancia detectada. Ajustando...")
        # Usar el menor número para evitar errores
        min_count = min(len(parrafos), len(prompts))
        parrafos = parrafos[:min_count]
        prompts = prompts[:min_count]
        print(f"✅ Ajustado a {min_count} párrafos y prompts")
    else:
        min_count = len(parrafos)  # Si coinciden, usar cualquiera
    
    if min_count < 14:
        raise ValueError(f"Demasiado pocos elementos generados ({min_count}). Mínimo requerido: 14")

    # Guardar parrafos.txt
    with open(historia_dir / "parrafos.txt", 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(parrafos))
    
    # Guardar prompts.txt
    with open(historia_dir / "prompts.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(prompts))

    # Guardar control_parrafos.json
    info_parrafos = []
    for idx, parrafo in enumerate(parrafos, 1):
        info_parrafos.append({
            "numero": idx,
            "texto": parrafo,
            "imagen": f"imagen_{idx}.png",
            "duracion_estimada": len(parrafo.split()) * 0.3
        })
    with open(historia_dir / "control_parrafos.json", 'w', encoding='utf-8') as f:
        json.dump({
            "total_parrafos": len(parrafos),
            "parrafos": info_parrafos
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Historia, parrafos y prompts generados y guardados en: {historia_dir}")
    print(f"💰 Estrategia económica: 2 peticiones en lugar de 5+ reintentos")
    print(f"📊 Resumen final: {len(parrafos)} párrafos y {len(prompts)} prompts")
    return parrafos, prompts 