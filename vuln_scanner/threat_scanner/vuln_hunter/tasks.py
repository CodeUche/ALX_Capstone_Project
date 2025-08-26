from celery import shared_task
import nmap, json
import subprocess
from .models import ScanJob
from django.utils import timezone
import shutil


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

    if shutil.which("nmap") is None:
        scan.status = "FAILED"
        scan.result = "Nmap is not installed"
        scan.end_time = timezone.now()
        scan.save()
        return "Nmap is not installed"

    try:
        nm = nmap.PortScanner()
        args = SCAN_PROFILES.get(scan.scan_type, "-T4 -F")
        nm.scan(hosts=scan.target, arguments=args)

        # Make the report Human-readable.
        report_lines = []
        for host in nm.all_hosts():
            report_lines.append(f"Host: {host} ({nm[host].hostname()})")
            report_lines.append(f"State: {nm[host].state()}")
            for proto in nm[host].all_protocols():
                report_lines.append(f"Protocol: {proto}")
                for port in nm[host][proto].keys():
                    p = nm[host][proto][port]
                    line = f"Port {port}/{proto} - State: {p['state']}, Service: {p.get('name','')}"
                    report_lines.append(line)
            report_lines.append("-" * 40)

        scan.result = "\n".join(report_lines)
        scan.status = "COMPLETED"
        scan.end_time = timezone.now()
        scan.save()
        return scan.result

    except Exception as e:
        scan.status = "FAILED"
        scan.result = str(e)
        scan.completed_at = timezone.now()
        scan.save()
        return str(e)


@shared_task(bind=True)
def run_whatweb_scan(self, scan_id):
    scan = ScanJob.objects.get(id=scan_id)
    scan.start_time = timezone.now()
    scan.status = "RUNNING"
    scan.save()

    try:
        result = subprocess.check_output(
            ["whatweb", scan.target], stderr=subprocess.STDOUT
        ).decode("utf-8")

        scan.result = result
        scan.status = "COMPLETED"
        scan.end_time = timezone.now()
        scan.save()
        return result

    except Exception as e:
        scan.status = "FAILED"
        scan.result = str(e)
        scan.end_time = timezone.now()
        scan.save()
        return str(e)
