from celery import shared_task
import nmap, json
import subprocess
from .models import ScanJob
from django.utils import timezone
import shutil


# Plugin definitions

PLUGIN_DESCRIPTIONS = {
    "WordPress": "WordPress CMS detected",
    "Apache": "Apache Web Server",
    "Nginx": "Nginx Web Server",
    "PHP": "PHP scripting language",
    "MySQL": "MySQL database",
    "Redis": "Redis key-value store",
    "MongoDB": "MongoDB database",
    "PostgreSQL": "PostgreSQL database",
    "Node.js": "Node.js runtime environment",
    "Python": "Python programming language",
    "Ruby": "Ruby programming language",
    "Java": "Java programming language",
    "Go": "Go programming language",
    "C++": "C++ programming language",
    "C#": "C# programming language",
    "Swift": "Swift programming language",
}

# All the scan profile dictionary
SCAN_PROFILES = {
    "fast": "-T4 -F",
    "aggressive": "-T4 -A -v",
    "udp": "-sU --top-ports 100",
    "full": "-p- -sV -sC",
    "stealth": "-sS -T3",
}


# Define a function to run Nmap scan
@shared_task
def run_nmap_scan(scan_id, scan_type):
    scan = ScanJob.objects.get(id=scan_id)
    scan.start_time = timezone.now()
    scan.status = "RUNNING"
    scan.save()

    if shutil.which("nmap") is None:
        scan.status = "FAILED"
        scan.result_text = "Nmap is not installed"
        scan.end_time = timezone.now()
        scan.save()
        return {"error": "Nmap is not installed"}

    try:
        nm = nmap.PortScanner()
        args = SCAN_PROFILES.get(scan_type, "-T4 -F")
        nm.scan(hosts=scan.target, arguments=args)

        # For structured frontend display
        ports = []
        # For human-readable text
        report_lines = []

        for host in nm.all_hosts():
            report_lines.append(f"Host: {host} ({nm[host].hostname()})")
            report_lines.append(f"State: {nm[host].state()}")
            for proto in nm[host].all_protocols():
                report_lines.append(f"Protocol: {proto}")
                for port in nm[host][proto].keys():
                    p = nm[host][proto][port]
                    port_info = {
                        "number": port,
                        "state": p["state"],
                        "service": p.get("name", ""),
                        "description": PLUGIN_DESCRIPTIONS.get(
                            p.get("name", ""), "No description"
                        ),
                    }
                    ports.append(port_info)
                    report_lines.append(
                        f"Port {port}/{proto} - State: {p['state']}, Service: {p.get('name','')}"
                    )

            report_lines.append("-" * 40)

        # Save both formats in DB
        scan.result_text = "\n".join(report_lines)
        scan.result_json = {"target": scan.target, "scan_type": "nmap", "ports": ports}
        scan.status = "COMPLETED"
        scan.end_time = timezone.now()
        scan.save()

        return scan.result_json

    except Exception as e:
        scan.status = "FAILED"
        scan.result_text = str(e)
        scan.result_json = {"error": str(e)}
        scan.end_time = timezone.now()
        scan.save()
        return scan.result_json


# Define a function to run whatweb scan
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
