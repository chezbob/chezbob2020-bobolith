from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from chezbob.bobolith.apps.appliances import routing as appliances_routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            appliances_routing.websocket_urlpatterns
        )
    )
})
