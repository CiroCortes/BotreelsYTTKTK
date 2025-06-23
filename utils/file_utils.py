import re
import unicodedata

def sanitizar_titulo_para_directorio(titulo: str) -> str:
    """
    Limpia y sanea un título para que sea un nombre de directorio válido y consistente en cualquier SO.
    - Convierte a minúsculas.
    - Elimina acentos y caracteres especiales.
    - Reemplaza espacios y guiones con un guion bajo.
    - Elimina cualquier caracter que no sea letra, número o guion bajo.
    """
    # Normalizar para descomponer acentos (NFD)
    titulo_normalizado = unicodedata.normalize('NFD', titulo.lower())
    # Eliminar diacríticos (marcas de acentos)
    titulo_sin_acentos = "".join(c for c in titulo_normalizado if unicodedata.category(c) != 'Mn')
    
    # Reemplazar espacios y caracteres problemáticos con guion bajo
    titulo_limpio = re.sub(r'[\s\W-]+', '_', titulo_sin_acentos)
    
    # Eliminar guiones bajos al principio o al final
    titulo_limpio = titulo_limpio.strip('_')
    
    return titulo_limpio 