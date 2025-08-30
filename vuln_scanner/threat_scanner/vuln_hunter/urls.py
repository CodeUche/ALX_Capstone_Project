from django.urls import path
from . import views

urlpatterns = [
    path("scan/", views.scan_target, name="scan_form"),
    path("scan/status/<str:scan_id>/", views.scan_status, name="scan_status"),
    path("scan/submitted/<str:scan_id>/", views.scan_submitted, name="scan_submitted"),
    path("scan/result/<str:scan_id>/", views.scan_result, name="scan_result"),
    
    # APU endpoints (CSRF-exempt, for Postman)
    path("api/scan", views.api_scan_target, name="api_scan"),
    path("api/status/<str:scan_id>/", views.api_scan_status, name="api_scan_status"),
]
