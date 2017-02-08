import pathlib

from .views import index

PROJECT_ROOT = pathlib.Path(__file__).parent

def setup_routes(app):
    app.router.add_get('/', index, name='main')
    app.router.add_static(
        '/static/',
        path=str(PROJECT_ROOT / 'static'),
        name='static'
    )
