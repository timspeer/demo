from django.urls import path, re_path
from . import views

app_name = 'accounting'
urlpatterns = [
    re_path(r'^[a-z]{4,}/$', views.accounting_index, name='accounting_index'),
    re_path(r'^[a-z]{4,}/create/$',  views.create_record, name='create'),
    re_path(r'^[a-z]{4,}/update/$',  views.update_record, name='update'),
    re_path(r'^[a-z]{4,}/remove/$',  views.remove_record, name='remove'),
    re_path(r'^[a-z]{4,}/fill/$',  views.fill_database, name='fill_database'),
    re_path(r'^[a-z]{4,}/ajax/$',  views.ajax, name='ajax'),
    re_path(r'^[a-z]{4,}/distribute/$',  views.distribute, name='distribute'),
]