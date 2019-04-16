from django.conf.urls import url
from . import views
import app.views
from esper.lib.views import VIEWS

urlpatterns = VIEWS + [
    url(r'^api/search', views.search, name='search'),
    url(r'^$', views.index, name='index')
]
