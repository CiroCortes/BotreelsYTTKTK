# Bot Creador de Shorts - Generador Automático de Videos

Un sistema completo para generar automáticamente videos cortos (shorts) a partir de historias bíblicas, utilizando inteligencia artificial para la generación de texto, imágenes y síntesis de voz.

## 🏗️ Arquitectura del Proyecto

El proyecto utiliza una arquitectura de **Capas de Servicio y Repositorio** con clientes de red desacoplados:

```
bot_creador_de_short/
├── app/
│   ├── models/          # Modelos de datos (Historia, Imagen, Video)
│   ├── services/        # Lógica de negocio (HistoriaService, ImagenService, etc.)
│   ├── network/         # Clientes de APIs externas (Gemini, Google TTS, etc.)
│   ├── workflows/       # Orquestación de flujos de trabajo
│   └── utils/           # Utilidades compartidas
├── config/
│   └── credentials/     # Credenciales (NO subir a Git)
├── historias/           # Historias generadas y sus recursos
├── scripts/             # Puntos de entrada de la aplicación
└── tests/               # Tests unitarios
```

## 🚀 Características

- **Generación de Historias**: Usando Gemini AI para crear narrativas bíblicas
- **Generación de Imágenes**: Múltiples proveedores (Leonardo, Vertex AI, HuggingFace, Stable Diffusion)
- **Síntesis de Voz**: Google Cloud Text-to-Speech
- **Creación de Videos**: Automatizada con efectos y música
- **Arquitectura Modular**: Fácil mantenimiento y extensión

## 📋 Requisitos

- Python 3.8+
- CUDA (opcional, para Stable Diffusion local)
- Credenciales de APIs externas

## ⚙️ Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciales

Crear la carpeta `config/credentials/` y agregar los archivos necesarios:

```
config/credentials/
├── gemini_api_key.txt           # Clave de Gemini AI
├── leonardo_api_key.txt         # Clave de Leonardo AI
├── vertex_ai_credentials.json   # Credenciales de Google Cloud
└── n8n-yt-458902-7993e2a59b32.json  # Cuenta de servicio Google
```

**⚠️ IMPORTANTE**: La carpeta `config/credentials/` está en `.gitignore` para proteger tus credenciales.

### 3. Configurar Variables de Entorno (Opcional)

```bash
export HF_HOME="C:/stable-diffusion-cache"  # Para Stable Diffusion
export GOOGLE_APPLICATION_CREDENTIALS="config/credentials/vertex_ai_credentials.json"
```

## 🎯 Uso

### Ejecutar el Pipeline Principal

```bash
python scripts/main.py
```

### Generar una Historia Específica

```python
from app.services.historia_service import HistoriaService
from app.services.imagen_service import ImagenService
from app.services.audio_service import AudioService
from app.services.video_service import VideoService

# Inicializar servicios
historia_service = HistoriaService()
imagen_service = ImagenService()
audio_service = AudioService()
video_service = VideoService()

# Generar historia
titulo = "La historia de David y Goliat"
historia = historia_service.generar_historia(titulo)

# Generar imágenes
imagenes = imagen_service.generar_imagenes_para_historia(titulo, historia.prompts, "leonardo")

# Generar audios
audio_service.generar_audios_para_historia(historia_dir, historia.parrafos)

# Crear video
video = video_service.crear_video_para_historia(titulo)
```

## 🔧 Proveedores de Imágenes

El sistema soporta múltiples proveedores de generación de imágenes:

- **Leonardo AI**: `modo_imagenes="leonardo"`
- **Google Vertex AI**: `modo_imagenes="vertex"`
- **HuggingFace FLUX**: `modo_imagenes="huggingface"`
- **Stable Diffusion Local**: `modo_imagenes="stable_diffusion"`

## 📁 Estructura de Archivos Generados

Cada historia se organiza en su propia carpeta:

```
historias/nombre_de_la_historia/
├── parrafos.txt              # Texto de la historia
├── prompts.txt               # Prompts para imágenes
├── control_parrafos.json     # Metadatos de párrafos
├── audios/
│   ├── voz_parrafo_1.mp3
│   ├── voz_parrafo_2.mp3
│   └── ...
├── imagen_1.png
├── imagen_2.png
└── video_final.mp4
```

## 🔒 Seguridad

- **Credenciales**: Nunca subir a Git
- **Archivos sensibles**: Protegidos por `.gitignore`
- **APIs**: Usar rate limiting y manejo de errores
- **Datos**: Validación en cada capa

## 🧪 Testing

```bash
# Ejecutar tests
python -m pytest tests/

# Tests específicos
python -m pytest tests/test_historia_service.py
```

## 📈 Monitoreo y Logs

El sistema incluye logging detallado para:
- Generación de historias
- Creación de imágenes
- Síntesis de voz
- Creación de videos
- Errores y excepciones

## 🔄 Migración y Mantenimiento

### Arquitectura Anterior vs Nueva

**Antes**: Lógica mezclada en `utils/`
**Ahora**: Separación clara en capas:
- `app/network/`: Clientes de APIs externas
- `app/services/`: Lógica de negocio
- `app/models/`: Estructuras de datos
- `app/workflows/`: Orquestación

### Agregar Nuevo Proveedor

1. Crear cliente en `app/network/nuevo_proveedor_client.py`
2. Implementar método `generar_imagen()`
3. Agregar opción en `ImagenService`
4. Actualizar documentación

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Para reportar bugs o solicitar features:
1. Crear issue en GitHub
2. Incluir logs y configuración
3. Describir pasos para reproducir

## 🔮 Roadmap

- [ ] Soporte para más idiomas
- [ ] Integración con más proveedores de IA
- [ ] Interfaz web
- [ ] API REST
- [ ] Docker containerization
- [ ] Kubernetes deployment 