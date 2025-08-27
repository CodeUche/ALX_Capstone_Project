from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("scan/form/", views.scan_target, name="scan_form"),
    path("scan/status/<str:task_id>/", views.scan_status, name="scan_status"),
    path("scan/submitted/<str:task_id>/", views.scan_submitted, name="scan_submitted"),
    path("scan/result/<str:task_id>/", views.scan_result, name="scan_result"),
]
