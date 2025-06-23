from typing import List

class Historia:
    """
    Modelo de datos para una historia.
    """
    def __init__(self, titulo: str, parrafos: List[str], prompts: List[str]):
        self.titulo = titulo
        self.parrafos = parrafos
        self.prompts = prompts

    @classmethod
    def from_files(cls, titulo: str, parrafos_path: str, prompts_path: str):
        """Crea una instancia de Historia leyendo los archivos de párrafos y prompts."""
        with open(parrafos_path, 'r', encoding='utf-8') as f:
            parrafos = [p.strip() for p in f.read().split('\n\n') if p.strip()]
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts = [p.strip() for p in f.read().split('\n') if p.strip()]
        return cls(titulo, parrafos, prompts) 