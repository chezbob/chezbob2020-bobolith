import importlib

from channels.db import database_sync_to_async
from django.urls import path

from .models import Appliance


def get_appliance(uuid):
    return Appliance.objects.get(pk=uuid)


def dispatch_appliance(scope):
    kwargs = scope['url_route']['kwargs']
    uuid = kwargs['appliance_uuid']

    [consumer_path] = Appliance.objects.values_list('consumer').get(pk=uuid)

    # Ensure we have the most recent version (even if we have hot-reloading).
    importlib.invalidate_caches()

    [module_name, klass_name] = consumer_path.rsplit('.', 1)
    module = importlib.import_module(module_name)
    klass = getattr(module, klass_name)

    return klass(scope)


websocket_urlpatterns = [
    path('appliance/ws/<uuid:appliance_uuid>/', dispatch_appliance)
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
