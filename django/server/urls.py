from django.conf.urls import url
from . import views
import scripts.views
from esper.views import VIEWS

urlpatterns = VIEWS + [
    url(r'^api/search', views.search, name='search'),
    url(r'^$', views.index, name='index')
]
