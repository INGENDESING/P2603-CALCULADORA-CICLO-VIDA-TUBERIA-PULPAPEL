from a2wsgi import ASGIMiddleware
from webapp.main import app as fastapi_app

# Compatibilidad con Render que ejecuta 'gunicorn app:app' por defecto
app = ASGIMiddleware(fastapi_app)
