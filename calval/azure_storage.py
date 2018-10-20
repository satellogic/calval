import itertools as it
try:
    from azure.storage.blob import BlockBlobService
except ImportError:  # pragma: no cover
    BlockBlobService = None
from calval.normalized_scene import NormalizedSceneId, URLScene


def _parse_cstring(cstring):
    parsed = {}
    for line in cstring.split(';'):
        key, val = line.strip().split('=', maxsplit=1)
        parsed[key] = val
    return parsed


def _cstring_endpoint(cstring):
    data = _parse_cstring(cstring)
    endpoint = data.get('BlobEndpoint')
    if endpoint is None:
        endpoint = '{DefaultEndpointsProtocol}://{AccountName}.blob.{EndpointSuffix}'.format(**data)
    return endpoint


class AzureStorage:
    def __init__(self, connection_string, container, prefix=''):
        self.connection_string = connection_string
        self.endpoint = _cstring_endpoint(connection_string)
        self.container = container
        self.prefix = prefix
        if BlockBlobService:
            self.service = BlockBlobService(connection_string=connection_string)
        else:  # pragma: no cover
            self.service = None

    def public_url_prefix(self):
        return '{}/{}/{}'.format(self.endpoint, self.container, self.prefix)

    def _iter_blobnames(self, prefix):
        return (blob.name
                for blob in self.service.list_blobs(
                        self.container, prefix=prefix, delimiter='/'))

    def query(self, **kwargs):
        assert self.service, 'Missing module: azure.storage.blob'
        parts = [kwargs.pop(field, None)
                 for field in NormalizedSceneId.tuple_type._fields]
        prefixes = [self.prefix]
        for part in parts:
            if part is None:
                prefixes = list(it.chain.from_iterable(map(self._iter_blobnames, prefixes)))
            else:
                if isinstance(part, str):
                    part = [part]
                prefixes = list(pref + term + '/'
                                for pref, term in it.product(prefixes, part))
        # If the last iteration did not query against the storage, we need to filter
        # (query without the trailing /) to see if it exists
        if parts[-1] is not None:
            prefixes = [pref for pref in prefixes
                        if any(self._iter_blobnames(pref[:-1]))]

        scenes = []
        for pref in prefixes:
            scene_id = NormalizedSceneId.from_str(pref[len(self.prefix):-1], separator='/')
            scenes.append(URLScene(self.public_url_prefix() + scene_id.metadata_path()))
        return scenes
