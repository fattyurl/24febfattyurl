from django.urls import path
from . import views

urlpatterns = [
    path('shorten', views.shorten, name='api_shorten'),
    path('links', views.list_links, name='api_list_links'),
    path('links/<int:pk>', views.link_detail, name='api_link_detail'),
    path('links/<int:pk>/clicks', views.link_clicks, name='api_link_clicks'),
    path('bulk', views.bulk_create, name='api_bulk_create'),
    path('export', views.export_csv, name='api_export_csv'),
]
