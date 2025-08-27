from .models import ScanJob
from django.shortcuts import render, redirect
from .tasks import run_nmap_scan, run_whatweb_scan
from django.http import JsonResponse, HttpResponse
from celery.result import AsyncResult


# Create your views here.
def scan_target(request):
    if request.method == "POST":
        target = request.POST.get("target")
        scan_type = request.POST.get("scan_type", "fast").lower()

        if not target:
            return render(
                request, "scan_form.html", {"error": "Please provide a target."}
            )

        # Save scan job
        scan = ScanJob.objects.create(target=target, scan_type=scan_type)

        # Kick off Celery task
        if scan_type == "whatweb":
            task = run_whatweb_scan.delay(scan.id)
        else:
            task = run_nmap_scan.delay(scan.id, scan_type)

        # (optional) save task_id in DB if you want
        scan.task_id = task.id
        scan.save()

        # Redirect to "scan submitted" page so polling can begin
        return redirect("scan_submitted", task_id=task.id)

    # GET request → just render scan form
    return render(request, "scan_form.html")


def scan_submitted(request, task_id):
    """Renders page after scan submission."""
    return render(request, "scan_submitted.html", {"task_id": task_id})


def scan_status(request, task_id):
    """Check the current status of the Celery task."""
    task = AsyncResult(task_id)
    if task.state == "SUCCESS":
        # Task has completed, return the result
        return JsonResponse({"status": "SUCCESS", "result": task.result})
    elif task.state == "FAILURE":
        # Task has failed
        return JsonResponse({"status": "FAILURE"})
    else:
        # Task is still in progress
        return JsonResponse({"status": "PENDING"})


def scan_result(request, task_id):
    """Return the result once the scan is done."""
    result = AsyncResult(task_id)
    if result.ready():
        scan_data = result.result

        # Fallback in case of errors
        if not isinstance(scan_data, dict):
            scan_data = {"error": scan_data}

        return render(request, "scan_result.html", {"scan_result": result.result})
    else:
        return HttpResponse("Scan not finished yet. Please wait.")
