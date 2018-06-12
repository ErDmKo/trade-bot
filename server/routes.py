import aiohttp
import pathlib

from . import views

PROJECT_ROOT = pathlib.Path(__file__).parent

def setup_routes(app):
    app.router.add_get('/', views.index, name='main')
    res = app.router.add_resource('/api/order/{id:\d+}')
    res.add_route('GET', views.order_info)
    app.router.add_post('/api/order', views.order, name='order')
    app.router.add_get('/api/order', views.get_orders, name='get_order')
    app.router.add_get('/api/history', views.get_history, name='get_history')
    app.router.add_delete('/api/order', views.delete_orders, name='delete_order')
    app.router.add_get('/api/pairs', views.pairs, name='pairs')

    app.router.add_get('/api/ws_pairs', views.ws_pairs, name='ws_pairs')
    app.router.add_get('/api/ws_balance', views.ws_balance, name='ws_balance')
    app.router.add_get('/api/ws_order_book', views.ws_order_book, name='ws_order_book')
    app.router.add_get('/api/ws_trade_log', views.ws_trade_log, name='ws_trade_log')
    app.router.add_static(
        '/static/',
        path=str(PROJECT_ROOT / 'static'),
        name='static'
    )
