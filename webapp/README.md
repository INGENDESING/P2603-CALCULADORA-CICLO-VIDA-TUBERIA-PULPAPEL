# Aplicación web — P2603 SW-K60 Vida útil de tuberías

Aplicación interactiva para el cálculo de vida útil por corrosión-erosión en tuberías SS304 / SS304L / A53 Gr B, basada en la metodología del informe P2603-PR-INF-001 (convención 2026-06-12).

## Stack

- **Backend:** FastAPI + Pydantic + Uvicorn
- **Frontend:** HTML5 + JavaScript vanilla + Plotly (local)
- **Tests:** Python unittest / script de regresión independiente

## Requisitos

- Python 3.10+
- Entorno virtual del proyecto (`.venv`) con las dependencias instaladas:
  - `fastapi`
  - `uvicorn[standard]`
  - `pydantic`
  - `openpyxl` (para exportación Excel)

## Ejecutar en desarrollo

Desde la raíz del proyecto:

```powershell
cd "C:\Users\ingen\OneDrive\1.0 PROYECTOS DML\CARTON COLOMBIA\P2603 SW-K60\6.0 Evaluacion corrosion ss316l"
.venv/Scripts/python -m uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

Accesos:

- Frontend: http://127.0.0.1:8000/static/index.html (o http://127.0.0.1:8000/ redirige)
- Documentación API: http://127.0.0.1:8000/docs
- API base: http://127.0.0.1:8000/api

## Tests

```powershell
.venv/Scripts/python webapp/tests/test_modelo.py
```

El script compara 153 casos contra los valores publicados en el informe (SS304L §14, A53 §9, condición crítica 60 °C, ejemplo §11 y consistencia Anexo E). Tolerancia: ±1 año.

## Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/materiales` | Materiales, cédulas y diámetros soportados |
| GET | `/api/escenarios` | Escenarios de servicio con parámetros típicos |
| POST | `/api/calcular/vida-util` | Cálculo unitario de vida útil |
| POST | `/api/calcular/tabla` | Tabla paramétrica por NPS/cédula |
| POST | `/api/calcular/sensibilidad-fs` | Sensibilidad al factor de seguridad |
| GET | `/api/calcular/condicion-critica` | Condición crítica 60 °C calibrada |
| POST | `/api/export/csv` | Exportar tabla a CSV |
| POST | `/api/export/excel` | Exportar tabla a Excel |
| GET | `/api/descargas/informe` | Descargar informe P2603-PR-INF-001 Rev.1 (PDF) |
| GET | `/api/descargas/presentacion` | Descargar presentación P2603-PR-PPT-001 Rev.1 (PPTX) |

## Limitaciones y advertencias

- El modelo de sinergia erosión-corrosión `Ws ≈ 0` está justificado para `v < 3 m/s` y `Cs < 12 %`. La app genera advertencias cuando se exceden estos rangos.
- La corrección de temperatura tipo Arrhenius tiene incertidumbre ±30 %; se advierte cuando la temperatura de operación difiere más de 50 °C de la temperatura de referencia del escenario.
- El factor de atenuación por pulpa refinada `β` tiene rango representativo calibrado de 0,15–0,40; valores fuera de ese rango generan advertencia.
- La calibración de 60 °C (`k₀,ref = 0,0035`, `β = 0,25`) es específica de la condición crítica documentada y requiere validación con mediciones UT de planta.
- El factor de seguridad adoptado en el informe es `FS = 1,1`. Otros valores generan advertencia.

## Estructura

```
webapp/
├── main.py              # Punto de entrada FastAPI
├── api.py               # Endpoints REST
├── schemas.py           # Validación Pydantic
├── corrosion_model.py   # Motor de cálculo puro
├── static/
│   ├── index.html       # Frontend
│   ├── app.js           # Lógica del frontend
│   ├── style.css        # Estilos DML
│   └── plotly.min.js    # Plotly descargado localmente
└── tests/
    └── test_modelo.py   # Tests de regresión
```

## Despliegue en Render (desde GitHub)

El repositorio incluye `render.yaml` y `requirements.txt` para despliegue directo.

1. Subir el proyecto a un repositorio de GitHub.
2. En Render, crear un nuevo **Web Service** conectado al repositorio (idealmente como **Blueprint** para que lea `render.yaml`).
3. Comandos correctos:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn webapp.main:app --host 0.0.0.0 --port $PORT`
4. Una vez desplegado, acceder a la URL asignada por Render; `/` redirige al frontend.

### ⚠ Servicio existente con timeout (creado a mano)

Los Web Services de Render creados manualmente **no leen** el `Procfile` ni el `render.yaml`: el comando de arranque vive en el **Start Command del dashboard de Render**. Si el servicio responde con timeout estando "Live", verificar en *Settings → Start Command* que NO quede el comando antiguo `gunicorn wsgi:application ...` (puente WSGI que bloqueaba las peticiones) y reemplazarlo por:

```
uvicorn webapp.main:app --host 0.0.0.0 --port $PORT
```

Luego *Manual Deploy → Clear build cache & deploy*.

### Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `PORT` | 8000 | Puerto de escucha (Render lo sobrescribe automáticamente). |
| `PYTHON_VERSION` | 3.13.4 | Versión de Python en Render (definida en `render.yaml`). |

### Health check

Render verifica el endpoint `/health` para confirmar que la aplicación está activa.

## Descargas de entregables

Los endpoints `GET /api/descargas/informe` y `GET /api/descargas/presentacion` sirven los archivos de `webapp/static/downloads/`:

| Archivo | Origen |
|---|---|
| `P2603-PR-INF-001_Rev1.pdf` | `P2603-PR-INF-001/P2603-PR-INF-001.pdf` |
| `P2603-PR-PPT-001_Rev1.pptx` | `Presentacion/...Comparativa Sch 10S vs 40S_REV1.pptx` |

**Al emitir una nueva revisión del informe o la presentación, re-copiar el archivo a `webapp/static/downloads/` con el mismo nombre.**

## Notas de despliegue

- `allow_origins` está abierto (`["*"]`) para simplificar el despliegue inicial. Cuando se defina el dominio definitivo del cliente, restringir `allow_origins` en `webapp/main.py`.
- Plotly y las fuentes (Titillium Web, JetBrains Mono) se cargan por CDN; sin internet el frontend degrada a las fuentes del sistema y los gráficos no se renderizan.
- El puerto se lee de la variable de entorno `PORT` para compatibilidad con Render.
- En Windows local usar `uvicorn` como se indica en la sección de desarrollo (es el mismo comando que producción).
