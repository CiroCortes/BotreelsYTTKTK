from app.workflows.pipeline_workflow import ejecutar_pipeline

def main():
    print("Bienvenido al bot creador de short")
    # Aquí podrías mostrar el menú y leer la opción del usuario
    # Por ahora, solo ejecuta el pipeline en modo manual como ejemplo
    ejecutar_pipeline(modo="manual")

if __name__ == "__main__":
    main() 