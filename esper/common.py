from .logging import log
from .util import Timer, pcache, storage
from .notifier import Notifier

if get_ipython() is not None:
    from .jupyter import *
