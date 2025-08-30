from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ScanJob
from django.shortcuts import render, redirect, get_object_or_404
from .tasks import run_nmap_scan, run_whatweb_scan
from django.http import JsonResponse, HttpResponse
from celery.result import AsyncResult
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
        return redirect("scan_submitted", scan_id=scan.id)

    # GET request → just render scan form
    return render(request, "scan_form.html")


def scan_submitted(request, scan_id):
    """Renders page after scan submission."""
    return render(request, "scan_submitted.html", {"scan_id": scan_id})


def scan_status(request, scan_id):
    """Check the current status of the Celery task."""
    task = AsyncResult(scan_id)
    scan = ScanJob.objects.get(task_id=scan_id)  # Retrieve scan by task_id

    # Update status from Celery task state
    if task.state == "SUCCESS":
        scan.status = "COMPLETED"
        if isinstance(task.result, dict):
            scan.result_json = task.result.get("json", {})
            scan.result_text = task.result.get("text", "")
        else:
            scan.result_json = {}
            scan.result_text = str(task.result)
        scan.save()

        return JsonResponse(
            {
                "status": "COMPLETED",
                "result_json": scan.result_json,
                "result_text": scan.result_text,
            }
        )
    elif task.state == "FAILURE":
        scan.status = "FAILED"
        scan.save()
        return JsonResponse({"status": "FAILED", "error": task.result})
    else:
        scan.status = "RUNNING"
        scan.save()
        return JsonResponse({"status": "RUNNING"})


def scan_result(request, scan_id):
    """Return the result once the scan is done."""
    result = AsyncResult(scan_id)
    if result.ready():
        scan_data = result.result

        # Fallback in case of errors
        if not isinstance(scan_data, dict):
            scan_data = {"error": scan_data}

        return render(request, "scan_result.html", {"scan_result": scan_data})
    else:
        return HttpResponse("Scan not finished yet. Please wait.")


# API-based views (Postman / JSON)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_scan_target(request):
    """
    Start a scan via API (requires authentication).
    """
    target = request.data.get("target")
    scan_type = request.data.get("scan_type", "fast").lower()

    if not target:
        return Response({"error": "Target is required"}, status=400)

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

    return Response(
        {"message": "Scan started", "scan_id": scan.id, "task_id": task.id}, status=201
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_scan_status(request, scan_id):
    """
    Check scan status by scan_id (not task_id).
    """
    try:
        scan = ScanJob.objects.get(id=scan_id)
    except ScanJob.DoesNotExist:
        return Response({"error": "Scan not found"}, status=404)

    # Check Celery task status if task_id exists
    if scan.task_id:
        task = AsyncResult(scan.task_id)
        if task.state == "SUCCESS":
            scan.status = "COMPLETED"
            scan.result_json = task.result if isinstance(task.result, dict) else {}
            scan.result_text = str(task.result)
            scan.save()
        elif task.state == "FAILURE":
            scan.status = "FAILED"
            scan.save()

    return Response(
        {
            "scan_id": scan.id,
            "status": scan.status,
            "result_json": scan.result_json if scan.status == "COMPLETED" else None,
            "result_text": scan.result_text if scan.status == "COMPLETED" else None,
        }
    )
