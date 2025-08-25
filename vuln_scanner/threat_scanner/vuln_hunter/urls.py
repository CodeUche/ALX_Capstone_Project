from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("scan_result/", views.scan_target, name="scan_target"),
]
