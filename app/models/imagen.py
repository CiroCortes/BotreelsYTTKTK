from pathlib import Path

class Imagen:
    """
    Modelo de datos para una imagen generada.
    """
    def __init__(self, ruta: Path):
        self.ruta = ruta

    @classmethod
    def from_path(cls, ruta: Path):
        """Crea una instancia de Imagen desde una ruta de archivo."""
        return cls(ruta) 