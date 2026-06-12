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
2. En Render, crear un nuevo **Web Service** conectado al repositorio.
3. Seleccionar **Blueprint** o dejar que Render detecte `render.yaml`.
4. Render ejecutará:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn -w 2 -k uvicorn.workers.UvicornWorker webapp.main:app --bind 0.0.0.0:$PORT`
5. Una vez desplegado, acceder a la URL asignada por Render; `/` redirige al frontend.

### Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `PORT` | 8000 | Puerto de escucha (Render lo sobrescribe automáticamente). |

### Health check

Render verifica el endpoint `/health` para confirmar que la aplicación está activa.

## Notas de despliegue

- `allow_origins` está abierto (`["*"]`) para simplificar el despliegue inicial. Cuando se defina el dominio definitivo del cliente, restringir `allow_origins` en `webapp/main.py`.
- Plotly se sirve localmente (`webapp/static/plotly.min.js`); no requiere conexión a internet.
- El puerto se lee de la variable de entorno `PORT` para compatibilidad con Render.
- El comando `gunicorn` del `render.yaml` corre en Linux (Render). En Windows local, usar `uvicorn` como se indica en la sección de desarrollo.
