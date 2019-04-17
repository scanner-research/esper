from django.conf.urls import url

VIEWS = []

def register_view(regex, *args, **kwargs):
    def wrapper(fn):
        global VIEWS
        u = url(regex, *args, view=fn, **kwargs)
        VIEWS.append(u)
        return fn
    return wrapper
