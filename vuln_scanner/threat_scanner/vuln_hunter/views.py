from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ScanJob
from .serializers import ScanJobSerializer
from django.shortcuts import render
from .tasks import run_nmap_scan, run_whatweb_scan


# Create your views here.
def scan_target(request):
    if request.method == "POST":
        target = request.POST.get("target")
        scan_type = request.POST.get("scan_type", "fast").lower()
        scan_result = run_nmap_scan(target, scan_type)
        
        if not target:
            return render(request, "scan_target.html", {"error": "Please provide a target."})


        # This is the view that will trigger the tasks
        # Create a scan job in DB

        scan = ScanJob.objects.create(target=target, scan_type=scan_type)

        # Trigger Celery task

        if scan_type == "whatweb":
            run_whatweb_scan.delay(scan.id)
        else:
            run_nmap_scan.delay(scan.id)

        # Redirect to a page to check status or show "Scan submitted and in progress..."
        return render(request, "scan_target.html", {"scan": scan})