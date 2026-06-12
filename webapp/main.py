# -*- coding: utf-8 -*-
"""
Punto de entrada de la aplicación FastAPI.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .api import router

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="P2603 SW-K60 — Vida útil de tuberías",
    description="Aplicación de cálculo de vida útil por corrosión-erosión basada en P2603-PR-INF-001.",
    version="1.0.0",
)

# CORS: en producción Render se sirve desde el mismo dominio, por lo que CORS
# estricto no es necesario. Se deja abierto para desarrollo local y futuros
# dominios personalizados. Recomendación: restringir allow_origins cuando se
# defina el dominio definitivo del cliente.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints bajo /api
app.include_router(router, prefix="/api")

# Archivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def root():
    """Redirige al frontend."""
    return RedirectResponse(url="/static/index.html")


@app.get("/health", include_in_schema=False)
def health():
    """Health check para Render."""
    return JSONResponse({"status": "ok", "app": "p2603-sw-k60-webapp"})


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(STATIC_DIR / "favicon.ico") if (STATIC_DIR / "favicon.ico").exists() else RedirectResponse(url="/static/index.html")


def main():
    """Entrypoint para ejecución directa con `python -m webapp.main`."""
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("webapp.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
