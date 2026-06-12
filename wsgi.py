from a2wsgi import ASGIMiddleware
from webapp.main import app

application = ASGIMiddleware(app)
