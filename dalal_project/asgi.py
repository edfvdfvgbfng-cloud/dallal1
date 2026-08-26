"""
ASGI config for dalal_project project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')

application = get_asgi_application()

# WebSocket support (optional)
USE_WEBSOCKETS = os.getenv('USE_WEBSOCKETS', 'False').lower() == 'true'
if USE_WEBSOCKETS:
    try:
        from channels.routing import ProtocolTypeRouter, URLRouter
        from channels.auth import AuthMiddlewareStack
        from django.urls import path

        # Import routing configuration
        try:
            from dalal_project import routing
            websocket_urlpatterns = routing.websocket_urlpatterns
        except ImportError:
            try:
                from properties import routing
                websocket_urlpatterns = routing.websocket_urlpatterns
            except ImportError:
                websocket_urlpatterns = []

        if websocket_urlpatterns:
            application = ProtocolTypeRouter({
                "http": get_asgi_application(),
                "websocket": AuthMiddlewareStack(
                    URLRouter(
                        websocket_urlpatterns
                    )
                ),
            })
    except ImportError:
        pass
