# PixelForge

Pipeline de procesamiento de imágenes en Python con **Pillow**. Lee las fotos JPG/PNG
de una carpeta y genera:

1. **Thumbnails** cuadrados de 300×300 (recorte centrado).
2. Un **filtro de viñeta** (bordes oscurecidos).
3. Un **watermark** semitransparente `© PixelForge` abajo a la derecha.
4. Una **versión grande** (hasta 1600 px, sin recorte) con los mismos efectos.
5. Una **galería web** responsive (`index.html`) con visor de imágenes.

---

## Requisitos

- Python 3.10 o superior (probado con 3.12).
- Dependencias (definidas en `pyproject.toml`):
  - `Pillow >= 10.1`: procesamiento de imágenes (única dependencia de ejecución).
  - `pytest >= 8`: solo para los tests.

> Las dependencias deben pasar por revisión del equipo antes de instalarse.

## Instalación

Desde la carpeta del proyecto, en PowerShell:

```powershell
python -m venv .venv                      # crear el entorno virtual (una vez)
.\.venv\Scripts\Activate.ps1              # activarlo (cada terminal nueva)
python -m pip install -e ".[dev]"         # instalar PixelForge + Pillow + pytest
```

Si PowerShell bloquea la activación ("la ejecución de scripts está deshabilitada"):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

O sin activar, usando el Python del entorno directamente:
`.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`.

## Uso

1. Copia tus imágenes `.jpg`, `.jpeg` o `.png` en `input/`.
2. Ejecuta:

   ```powershell
   python -m pixelforge
   # o, con el entorno sin activar:
   .\.venv\Scripts\python.exe -m pixelforge
   ```

3. Abre `output\index.html` con doble clic (no necesita servidor).

Ejemplo de salida:

```
INFO: OK: coche.jpg -> thumbs/coche_jpg.jpg + full/coche_jpg.jpg 638x400
INFO: Listo: 1 procesadas, 0 omitidas. Salida en output
INFO: Galería: output\index.html
```

### Parámetros

| Opción | Por defecto | Descripción |
|---|---|---|
| `--input RUTA` | `input` | Carpeta con las imágenes de entrada (no recorre subcarpetas). |
| `--output RUTA` | `output` | Carpeta de salida. No puede ser la misma que la de entrada. |
| `--size PX` | `300` | Lado del thumbnail cuadrado. |
| `--full-size PX` | `1600` | Lado mayor máximo de la versión grande. `0` = no generarla. |
| `--vignette 0-1` | `0.6` | Intensidad de la viñeta. `0` = sin viñeta. |
| `--watermark TEXTO` | `© PixelForge` | Texto del watermark. Vacío = sin watermark. |
| `--opacity 0-1` | `0.5` | Opacidad del watermark. `0` = invisible. |
| `-v`, `--verbose` | — | Muestra mensajes de depuración. |
| `--version` | — | Muestra la versión. |

Ejemplos:

```powershell
python -m pixelforge --vignette 0.9 --opacity 0.8          # efectos más marcados
python -m pixelforge --size 200 --full-size 1200           # salidas más livianas
python -m pixelforge --watermark "© Mi Estudio 2026"       # texto propio
python -m pixelforge --input C:\Fotos\viaje --output C:\Fotos\viaje_web
```

### Códigos de salida

| Código | Significado |
|---|---|
| `0` | Correcto, aunque se hayan omitido algunos archivos dañados, o si no había imágenes. |
| `1` | La carpeta de entrada no existe, ninguna imagen se pudo procesar o falló la escritura de la galería. |
| `2` | Parámetros inválidos (p. ej. `--opacity 3`). |

## Qué se genera

```
output/
├── index.html      # galería
├── styles.css      # estilos de la galería
├── thumbs/         # thumbnails 300×300 con viñeta + watermark
│   └── coche_jpg.jpg
└── full/           # versión grande con viñeta + watermark
    └── coche_jpg.jpg
```

### La galería

- **Responsive:** 1 columna en celular y hasta 4–5 en escritorio (CSS Grid).
- **Visor:** al hacer clic en una tarjeta, la versión grande se abre encima de la galería,
  con botones anterior/siguiente (dan la vuelta) y un enlace "Abrir original".
- **Teclado:** `Esc` cierra el visor; `←` y `→` navegan.
- **Funciona sin JavaScript:** el visor usa CSS `:target`. El script solo añade los atajos.
- **Carga diferida:** los thumbnails cargan al hacer scroll y la imagen grande solo al abrir
  el visor.
- **Accesibilidad:** cada imagen lleva `alt`, la navegación por teclado se ve resaltada y las
  animaciones se desactivan si el sistema pide "reducir movimiento".
- **Diseño:** oscuro a propósito para que las fotos resalten. Los acentos van de brasa a magenta
  y violeta ("forja digital"). El fondo tiene una cuadrícula de píxeles y brillos animados,
  y las tarjetas entran escalonadas.

## Cómo funciona

```
input/*.jpg|png
   │  loader.py      busca archivos, corrige orientación EXIF, normaliza a RGB/RGBA
   ▼
imagen ─┬─ thumbnail.py  make_thumbnail → 300×300 recorte centrado
        └─ thumbnail.py  fit_within     → lado mayor ≤ 1600, sin recorte
   │  vignette.py    oscurece bordes (degradado radial)
   │  watermark.py   texto semitransparente abajo a la derecha
   ▼
output/thumbs + output/full
   │  gallery.py     index.html + styles.css
   ▼
output/index.html
```

| Módulo | Responsabilidad |
|---|---|
| `config.py` | Parámetros (`Config`) y su validación. |
| `cli.py` | Línea de comandos: parsea argumentos, ejecuta pipeline y galería. |
| `loader.py` | Encuentra imágenes y las abre de forma segura. |
| `thumbnail.py` | Thumbnail cuadrado y reducción de la versión grande. |
| `vignette.py` | Filtro de viñeta. |
| `watermark.py` | Watermark de texto. |
| `pipeline.py` | Orquesta los pasos por imagen y nombra/guarda las salidas. |
| `gallery.py` | Genera la galería desde `templates/`. |

## Decisiones de diseño

- **Recorte centrado en el thumbnail** (`ImageOps.fit`): todas las tarjetas miden lo mismo
  y la cuadrícula queda pareja. A cambio, en fotos muy anchas se pierden los lados. Por eso
  existe la versión grande sin recorte.
- **Orden thumbnail → viñeta → watermark:** el texto va al final para que la viñeta no lo
  oscurezca.
- **La viñeta y el watermark se aplican después de redimensionar:** así el efecto se ve igual
  en cualquier tamaño de foto original, y el procesamiento es más rápido.
- **Nombres de salida sin choques:** `foto.jpg` → `foto_jpg.jpg` y `foto.png` → `foto_png.png`,
  para que dos archivos con el mismo nombre base no se sobrescriban.
- **Formato:** los PNG siguen siendo PNG (conservan transparencia); JPG/JPEG salen como JPG
  (calidad 88, progresivo).
- **Orientación EXIF:** las fotos de celular giradas se enderezan antes de procesarse.
- **Archivos dañados:** se omiten con un aviso y el resto continúa.
- **La versión grande nunca se amplía:** una foto de 638×400 queda en 638×400.
- **El watermark escala con la imagen** (≈7 % del lado menor) y se reduce si el texto no cabe.
  Usa Arial o DejaVu si existen y, si no, la fuente que trae Pillow.
- **Una sola dependencia:** la viñeta usa `Image.radial_gradient` (sin numpy) y la galería usa
  `string.Template` (sin Jinja2).

## Tests

```powershell
python -m pytest            # o .\.venv\Scripts\python.exe -m pytest
```

Son 69 tests en `__tests__/`. Usan imágenes sintéticas generadas en carpetas temporales, así
que no dependen de `input/`. Cubren la configuración, la carga (incluye EXIF, PNG con alfa y
archivos dañados), el thumbnail, la viñeta, el watermark, el pipeline completo, la CLI y la
galería (escape de nombres raros, enlaces válidos y navegación del visor).

## Limitaciones conocidas y mejoras posibles

- **Salidas viejas:** si borras una imagen de `input/`, sus archivos en `output/thumbs` y
  `output/full` quedan. La galería no los muestra (se genera solo con lo procesado en esa
  ejecución). Para limpiar, borra `output/` antes de ejecutar.
- **Acentos en Git Bash:** en la consola de Git Bash los mensajes con acentos pueden verse
  rotos. En PowerShell y CMD se ven bien.
- **Imágenes grandes:** cada imagen se procesa en memoria. Pillow rechaza imágenes
  sospechosamente enormes (protección contra "decompression bombs"); esas se omiten con aviso.
- **Mejoras posibles:** procesamiento en paralelo, subcarpetas de entrada, más formatos (WebP),
  procesar solo imágenes nuevas o modificadas, y limpieza automática de salidas huérfanas.

## Pendientes del proyecto

- Inicializar el control de versiones (`git init`) y trabajar en una rama distinta de `main`.
- Revisión del equipo de las dependencias declaradas en `pyproject.toml`.
