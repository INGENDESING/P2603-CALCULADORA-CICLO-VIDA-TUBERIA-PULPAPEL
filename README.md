# P2603 SW-K60 — Evaluación de vida útil de tuberías

Aplicación web interactiva para el cálculo de vida útil por corrosión-erosión en tuberías de acero inoxidable SS304 / SS304L y acero al carbono A53 Gr B. Basada en la metodología del informe técnico **P2603-PR-INF-001** Rev.1 (convención 2026-06-12).

## Contenido del repositorio

```
.
├── webapp/                    # Aplicación web FastAPI + frontend HTML/JS
├── requirements.txt           # Dependencias Python para Render
├── render.yaml                # Especificación de despliegue en Render
└── README.md                  # Este archivo
```

## Aplicación web

La carpeta `webapp/` contiene una aplicación web con backend **FastAPI** y frontend **HTML/JavaScript** que permite calcular la vida útil de tuberías bajo distintos escenarios de servicio, materiales, cédulas y condiciones de operación.

### Ejecutar en desarrollo (Windows)

```powershell
cd "C:\Users\ingen\OneDrive\1.0 PROYECTOS DML\CARTON COLOMBIA\P2603 SW-K60\6.0 Evaluacion corrosion ss316l"
.venv\Scripts\python -m uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

Accesos locales:

- Frontend: http://127.0.0.1:8000/static/index.html
- Documentación API: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### Tests de regresión

```powershell
.venv\Scripts\python webapp\tests\test_modelo.py
```

El script compara 153 casos contra los valores publicados en el informe. Resultado esperado: **0 discrepancias**.

## Despliegue en Render (desde GitHub)

### 1. Subir a GitHub

```powershell
git init
git add .
git commit -m "P2603 SW-K60 webapp v1.0"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

> Reemplazar `TU_USUARIO/TU_REPO` por el usuario y nombre del repositorio.

### 2. Crear servicio en Render

1. Ir a [render.com](https://render.com) e iniciar sesión.
2. **New → Web Service → Connect a repository**.
3. Seleccionar el repositorio de GitHub.
4. Configurar el servicio (o crear como **Blueprint** para que lea `render.yaml`):
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn webapp.main:app --host 0.0.0.0 --port $PORT`
   - **Health check path:** `/health`
5. Hacer clic en **Deploy**.

> **Importante (fix de timeout):** si el servicio ya existe y fue creado a mano, Render NO lee
> el `Procfile` ni el `render.yaml`; el Start Command vive en el dashboard. Cambiar ahí el
> comando antiguo `gunicorn wsgi:application ...` por el comando `uvicorn` anterior y
> redesplegar con *Clear build cache & deploy*.

Render asignará una URL pública tipo:

```
https://p2603-sw-k60-webapp.onrender.com
```

La raíz (`/`) redirige al frontend interactivo.

### 3. Después del despliegue

- Verificar que `/health` responda `{"status":"ok"}`.
- Probar el cálculo unitario y la tabla paramétrica.
- Cuando se defina el dominio definitivo del cliente, restringir `allow_origins` en `webapp/main.py` por seguridad.

## Dependencias

Las dependencias de la webapp están en `requirements.txt`:

- `fastapi==0.136.3`
- `uvicorn[standard]==0.49.0`
- `pydantic==2.13.4`
- `openpyxl==3.1.5`


## Endpoints principales de la API

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/materiales` | Materiales, cédulas y diámetros |
| GET | `/api/escenarios` | Escenarios de servicio |
| POST | `/api/calcular/vida-util` | Cálculo unitario de vida útil |
| POST | `/api/calcular/tabla` | Tabla paramétrica |
| POST | `/api/calcular/sensibilidad-fs` | Sensibilidad al factor de seguridad |
| GET | `/api/calcular/condicion-critica` | Condición crítica 60 °C calibrada |
| POST | `/api/export/csv` | Exportar tabla a CSV |
| POST | `/api/export/excel` | Exportar tabla a Excel |
| GET | `/api/descargas/informe` | Descargar informe P2603-PR-INF-001 Rev.1 (PDF) |
| GET | `/api/descargas/presentacion` | Descargar presentación P2603-PR-PPT-001 Rev.1 (PPTX) |

Documentación interactiva disponible en `/docs` una vez desplegada.

## Notas técnicas importantes

- El modelo está basado en la metodología del informe **P2603-PR-INF-001** (convención 2026-06-12).
- Los resultados incluyen advertencias de validez cuando se exceden rangos documentados (velocidad, consistencia, temperatura, factor de seguridad, etc.).
- La calibración de 60 °C (`k₀,ref = 0,0035`, `β = 0,25`) es específica de la condición crítica documentada y requiere validación con mediciones UT de planta.
- El factor de seguridad adoptado en el informe es **FS = 1,1**; otros valores generan advertencia.

## Entregables finales del proyecto

- `webapp/static/downloads/P2603-PR-INF-001_Rev1.pdf` — Informe técnico Rev.1 (75 págs.)
- `webapp/static/downloads/P2603-PR-PPT-001_Rev1.pptx` — Presentación Rev.1 (34 slides)
- Aplicación web interactiva

## Aviso legal

Esta aplicación es una herramienta de cálculo basada en un modelo ingenieril con incertidumbres documentadas. Los resultados no sustituyen el juicio de un ingeniero calificado, inspecciones de planta ni la verificación contra normas aplicables.
