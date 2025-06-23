from pathlib import Path

class Video:
    """
    Modelo de datos para un video generado.
    """
    def __init__(self, ruta: Path):
        self.ruta = ruta

    @classmethod
    def from_path(cls, ruta: Path):
        """Crea una instancia de Video desde una ruta de archivo."""
        return cls(ruta) 