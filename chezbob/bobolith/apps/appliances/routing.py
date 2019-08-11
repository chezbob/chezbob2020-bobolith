import importlib
from pprint import pprint

from django.urls import path

from .models import Appliance


def dispatch_appliance(scope):
    kwargs = scope['url_route']['kwargs']
    appliance_uuid = kwargs['appliance_uuid']

    appliance = Appliance.objects.get(pk=appliance_uuid)

    importlib.invalidate_caches()

    [module_name, klass_name] = appliance.consumer.rsplit('.', 1)
    module = importlib.import_module(module_name)
    klass = getattr(module, klass_name)

    return klass(scope)


websocket_urlpatterns = [
    path('ws/<uuid:appliance_uuid>/', dispatch_appliance)
]

"""
Schema of scope is:

cookies: Dict[str, str]
headers: List[Tuple[str, str]]
path: str
path_remaining: str
query_string: bytes
server: Tuple[str, int] (but it's actually a list)
session: LazyObject[Session]
subprotocols: List[?]
type: str
url_route: {
    args: ...
    kwargs: ...
}
user: UserLazyObject

"""