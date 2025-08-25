import nmap
from celery import Celery, shared_task


# All the scan profile dictionary
SCAN_PROFILES = {
    "fast": "-T4 -F",
    "aggressive": "-T4 -A -v",
    "udp": "-sU --top-ports 100",
    "full": "-p- -sV -sC",
    "stealth": "-sS -T3",
}


@shared_task
def run_nmap_scan(target, profile="fast"):
    nm = nmap.PortScanner()

    if profile not in SCAN_PROFILES:
        raise ValueError(
            f"Invalid scan profile: {profile}. Available profiles to choose from: {list(SCAN_PROFILES.keys())}"
        )

    args = SCAN_PROFILES[profile]
    result = nm.scan(hosts=target, arguments=args)
    return result


# Fast scan
run_nmap_scan.delay("192.168.1.1", "fast")

# Aggressive scan
run_nmap_scan.delay("alx-africa.com", "aggressive")

