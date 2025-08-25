from django.shortcuts import render
from .tasks import run_nmap_scan


# Create your views here.
def scan_target(request):
    if request.method == "POST":
        target = request.POST.get("target")
        scan_type = request.POST.get("scan_type")
        scan_result = run_nmap_scan(target, scan_type)
        return render(
            request, "vuln_hunter/scan_result.html", {"scan_result": scan_result}
        )
    return render(request, "vuln_hunter/scan_form.html")
