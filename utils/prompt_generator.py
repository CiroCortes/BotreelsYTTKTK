import pandas as pd

def calcular_duracion_parrafo(parrafo: str) -> float:
    """
    Calcula la duración aproximada de un párrafo en segundos.
    Asume una velocidad de lectura promedio de 150 palabras por minuto.
    
    Args:
        parrafo: El texto del párrafo
        
    Returns:
        float: Duración estimada en segundos
    """
    palabras = len(parrafo.split())
    palabras_por_segundo = 150 / 60  # 150 palabras por minuto
    duracion = palabras / palabras_por_segundo
    
    # Ajustar a un mínimo de 5 segundos y máximo de 6 segundos
    return max(5.0, min(6.0, duracion))

def calcular_prompts_necesarios(parrafos: list[str]) -> int:
    """
    Calcula el número de prompts necesarios basado en la duración total de los párrafos.
    
    Args:
        parrafos: Lista de párrafos de la historia
        
    Returns:
        int: Número de prompts necesarios
    """
    duracion_total = sum(calcular_duracion_parrafo(p) for p in parrafos)
    # Cada prompt debe cubrir aproximadamente 5-6 segundos
    num_prompts = int(duracion_total / 5.5) + 1  # +1 para asegurar cobertura completa
    return max(1, num_prompts)  # Mínimo 1 prompt

def procesar_prompts(respuesta: str, num_parrafos: int) -> tuple[list[str], list[str]]:
    """Procesa la respuesta de la IA y extrae los párrafos y prompts"""
    # Separar historia y prompts
    partes = respuesta.split("[PROMPTS]")
    if len(partes) != 2:
        raise ValueError("Formato de respuesta inválido")
    
    historia = partes[0].replace("[HISTORIA]", "").strip()
    prompts = partes[1].strip()
    
    # Procesar párrafos
    parrafos = [p.strip() for p in historia.split("|") if p.strip()]
    if len(parrafos) != num_parrafos:
        raise ValueError(f"Se esperaban {num_parrafos} párrafos, se encontraron {len(parrafos)}")
    
    # Procesar prompts
    prompts_lista = [p.strip() for p in prompts.split("#") if p.strip()]
    
    # Si faltan prompts, generar uno adicional basado en el último párrafo
    if len(prompts_lista) < num_parrafos:
        print(f"\n⚠️ Advertencia: Se generaron {len(prompts_lista)} prompts de {num_parrafos} necesarios")
        print("Generando prompt adicional basado en el último párrafo...")
        
        # Usar el último prompt como base y modificarlo
        ultimo_prompt = prompts_lista[-1]
        prompt_base = "Create a cinematic biblical scene with dramatic lighting and epic atmosphere. The scene should be ultra-realistic with divine glow and apocalyptic elements. Use hyper-detailed textures and 4K resolution. The style should combine Renaissance religious art with modern epic film visuals, inspired by Zack Snyder and Caravaggio. The scene should be shot on an ultra high-definition digital cinema camera with volumetric lighting, deep shadows, and celestial illumination. The composition should be vertical (9:16 aspect ratio) and include: "
        
        # Generar prompts adicionales basados en el último párrafo
        while len(prompts_lista) < num_parrafos:
            nuevo_prompt = f"{prompt_base}A continuation of the previous scene, maintaining the epic and dramatic atmosphere, with divine elements and apocalyptic undertones."
            prompts_lista.append(nuevo_prompt)
    
    return parrafos, prompts_lista

def guardar_prompts_en_excel(df: pd.DataFrame, idx: int, prompts: list[str]) -> None:
    """Guarda los prompts en el Excel, creando columnas dinámicamente si es necesario"""
    # Crear columnas de prompt si no existen
    for i in range(1, len(prompts) + 1):
        col_name = f"prompt{i}"
        if col_name not in df.columns:
            df[col_name] = ""
    
    # Guardar prompts
    for i, prompt in enumerate(prompts, 1):
        df.at[idx, f"prompt{i}"] = prompt