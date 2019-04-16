from .logging import log
from pickle_cache import PickleCache
import os
from storehouse import StorageConfig, StorageBackend


class Timer:
    def __init__(self, s, run=True):
        self._s = s
        self._run = run
        if run:
            log.debug('-- START: {} --'.format(s))

    def __enter__(self):
        self.start = now()

    def __exit__(self, a, b, c):
        t = int(now() - self.start)
        if self._run:
            log.debug('-- END: {} -- {:02d}:{:02d}:{:02d}'.format(
                self._s, int(t / 3600), int((t / 60) % 60),
                int(t) % 60))


pcache = PickleCache(cache_dir='/app/.cache')

ESPER_ENV = os.environ.get('ESPER_ENV')
BUCKET = os.environ.get('BUCKET')

if ESPER_ENV == 'google':
    storage_config = StorageConfig.make_gcs_config(BUCKET)
else:
    storage_config = StorageConfig.make_posix_config()
storage = StorageBackend.make_from_config(storage_config)
