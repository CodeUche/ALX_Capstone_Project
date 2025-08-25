from celery import Celery, shared_task
import nmap
import subprocess
from .models import ScanJob
from django.utils import timezone


# All the scan profile dictionary
SCAN_PROFILES = {
    "fast": "-T4 -F",
    "aggressive": "-T4 -A -v",
    "udp": "-sU --top-ports 100",
    "full": "-p- -sV -sC",
    "stealth": "-sS -T3",
}


@shared_task(bind=True)
def run_nmap_scan(self, scan_id):
    scan = ScanJob.objects.get(id=scan_id)
    scan.start_time = timezone.now()
    scan.status = "RUNNING"
    scan.save()

    try:
        nm = nmap.PortScanner()
        args = SCAN_PROFILES(scan.scan_type, "-T4 -F")
        result = nm.scan(hosts=scan.target, arguments=args)
        scan.result = result
        scan.status = "COMPLETED"
        scan.end_time = timezone.now()

    except Exception as e:
        scan.status = "FAILED"
        scan.result = str(e)

    scan.completed_at = timezone.now()
    scan.save()
    return scan.result


@shared_task(bind=True)
def run_whatweb_scan(self, scan_id):

    try:
        scan = ScanJob.Objects.get(id=scan_id)
        scan.status = "COMPLETED"
        scan.end_time = timezone.now()
        scan.save()

        result = subprocess.check_output(
            ["whatweb", scan.target], stderr=subprocess.STDOUT
        ).decode("utf-8")

        scan.result = result
        scan.status = "COMPLETED"
        scan.end_time = timezone.now()

    except Exception as e:
        scan.status = "FAILED"
        scan.result = str(e)

    scan.completed_at = timezone.now()
    scan.save()
    return scan.result
