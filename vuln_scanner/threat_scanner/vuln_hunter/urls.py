from django.urls import path
from . import views

urlpatterns = [
    path("scan/", views.scan_target, name="scan_form"),
    path("status/<str:task_id>/", views.scan_status, name="scan_status"),
    path("submitted/<str:task_id>/", views.scan_submitted, name="scan_submitted"),
    path("result/<str:task_id>/", views.scan_result, name="scan_result"),
   
    # APU endpoints (CSRF-exempt, for Postman)
    path("api/scan", views.api_scan_target, name="api_scan"),
    path("api/status/<str:task_id>/", views.api_scan_status, name="api_scan_status"),
    path("api/submitted/<str:task_id>/", views.api_scan_submitted, name="api_scan_submitted"),
    path("api/result/<str:task_id>/", views.api_scan_result, name="api_scan_result"),
]
