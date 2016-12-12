import aiohttp
import pathlib

from . import views

PROJECT_ROOT = pathlib.Path(__file__).parent

def setup_routes(app):
    app.router.add_get('/', views.index, name='main')
    app.router.add_post('/api/order', views.order, name='order')
    app.router.add_get('/api/pairs', views.pairs, name='pairs')
    app.router.add_get('/api/ws_pairs', views.ws_pairs, name='ws_pairs')
    app.router.add_get('/api/ws_order_book', views.ws_order_book, name='ws_order_book')
    app.router.add_static(
        '/static/',
        path=str(PROJECT_ROOT / 'static'),
        name='static'
    )
