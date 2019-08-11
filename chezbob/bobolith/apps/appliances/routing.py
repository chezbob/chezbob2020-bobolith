import importlib

from channels.db import database_sync_to_async
from django.urls import path

from .models import Appliance


# @database_sync_to_async
def get_appliance(uuid):
    return Appliance.objects.get(pk=uuid)


def dispatch_appliance(scope):
    kwargs = scope['url_route']['kwargs']
    appliance_uuid = kwargs['appliance_uuid']

    appliance = get_appliance(appliance_uuid)

    importlib.invalidate_caches()

    [module_name, klass_name] = appliance.consumer.rsplit('.', 1)
    module = importlib.import_module(module_name)
    klass = getattr(module, klass_name)

    return klass(scope, appliance)


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
