from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ScanJob
from django.shortcuts import render, redirect
from .tasks import run_nmap_scan, run_whatweb_scan
from django.http import JsonResponse, HttpResponse
from celery.result import AsyncResult
import json
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


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

        # Save task_id in DB
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
    scan = ScanJob.objects.get(task_id=task_id)  # Retrieve scan by task_id

    # Update status from Celery task state
    if task.state == "SUCCESS":
        scan.status = "COMPLETED"
        scan.save()
        return JsonResponse({"status": "COMPLETED", "result": task.result})
    elif task.state == "FAILURE":
        scan.status = "FAILED"
        scan.save()
        return JsonResponse({"status": "FAILED", "error": task.result})
    else:
        scan.status = "RUNNING"
        scan.save()
        return JsonResponse({"status": "RUNNING"})


def scan_result(request, task_id):
    """Return the result once the scan is done."""
    result = AsyncResult(task_id)
    if result.ready():
        scan_data = result.result

        # Fallback in case of errors
        if not isinstance(scan_data, dict):
            scan_data = {"error": scan_data}

        return render(request, "scan_result.html", {"scan_result": scan_data})
    else:
        return HttpResponse("Scan not finished yet. Please wait.")


# API-based views (Postman / JSON)
@csrf_exempt
@require_http_methods(["POST"])
def api_scan_target(request):

    # Start a scan via JSON API.
    try:
        data = json.loads(request.body.decode("utf-8"))
        target = data.get("target")
        scan_type = data.get("scan_type", "fast").lower()
    except Exception:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    if not target:
        return JsonResponse({"error": "Target is required"}, status=400)

    # Save scan job
    scan = ScanJob.objects.create(
        target=target, scan_type=scan_type, start_time=timezone.now(), status="QUEUED"
    )

    # Kick off Celery task
    if scan_type == "whatweb":
        task = run_whatweb_scan.delay(scan.id)
    else:
        task = run_nmap_scan.delay(scan.id, scan_type)

    # Save task_id in DB
    scan.task_id = task.id
    scan.save()

    return JsonResponse(
        {"message": "Scan started", "scan_id": scan.id, "task_id": task.id}, status=201
    )


@csrf_exempt
@require_http_methods(["GET"])
def api_scan_submitted(request, task_id):
    return JsonResponse({"message": "Scan submitted"})


@csrf_exempt
@require_http_methods(["GET"])
def api_scan_status(request, task_id):
    task = AsyncResult(task_id)
    scan = ScanJob.objects.get(task_id=task_id)  # Retrieve scan by task_id

    # Update status from Celery task state
    if task.state == "SUCCESS":
        scan.status = "COMPLETED"
        scan.save()
        return JsonResponse({"status": "COMPLETED", "result": task.result})
    elif task.state == "FAILURE":
        scan.status = "FAILED"
        scan.save()
        return JsonResponse({"status": "FAILED", "error": task.result})
    else:
        scan.status = "RUNNING"
        scan.save()
        return JsonResponse({"status": "RUNNING"})


@csrf_exempt
@require_http_methods(["GET"])
def api_scan_result(request, task_id):
    result = AsyncResult(task_id)
    if result.ready():
        scan_data = result.result

        # Fallback in case of errors
        if not isinstance(scan_data, dict):
            scan_data = {"error": scan_data}

        return JsonResponse(scan_data)
    else:
        return JsonResponse({"error": "Scan not finished yet. Please wait."})
