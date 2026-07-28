"""TCP connect port scanner, scoped to an authorized lab network (LAB_SCOPE)."""

import ipaddress
import logging
import os
import socket
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

DEFAULT_LAB_SCOPE = "192.168.137.0/24"
DEFAULT_THREADS = 64
MAX_THREADS = 256


def _lab_networks():
    raw = os.environ.get("LAB_SCOPE", DEFAULT_LAB_SCOPE)
    return [ipaddress.ip_network(cidr.strip(), strict=False) for cidr in raw.split(",") if cidr.strip()]


def validate_scope(target_ip: str) -> None:
    """target_ip가 IP 리터럴이고 LAB_SCOPE 대역 내에 있는지 검증. 아니면 ValueError."""
    try:
        ip = ipaddress.ip_address(target_ip)
    except ValueError:
        raise ValueError(f"target must be an IP literal, got: {target_ip!r}")

    if not any(ip in net for net in _lab_networks()):
        raise ValueError(f"target {target_ip} is out of scope (LAB_SCOPE)")


def _resolve_threads(threads):
    if threads is None:
        raw = os.environ.get("SCAN_THREADS", str(DEFAULT_THREADS))
        try:
            threads = int(raw)
        except ValueError:
            threads = DEFAULT_THREADS
    return max(1, min(threads, MAX_THREADS))


def recon_scan(target_ip, start_port=1, end_port=1023, threads=None, timeout=0.5):
    """
    Multithreaded TCP connect scan - well-known ports (0-1023)
    """
    validate_scope(target_ip)
    threads = _resolve_threads(threads)

    open_ports = []
    lock = threading.Lock()

    def scan_port(port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            result = s.connect_ex((target_ip, port))
            s.close()

            if result == 0:
                with lock:
                    open_ports.append(port)
                logger.info("%s:%d OPEN", target_ip, port)
        except OSError:
            pass

    logger.info("Scanning %s ports %d-%d (%d threads)...", target_ip, start_port, end_port, threads)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(scan_port, range(start_port, end_port + 1))

    return {
        "target": target_ip,
        "open_ports": sorted(open_ports),
        "scan_range": f"{start_port}-{end_port}",
        "status": "completed"
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 recon_scan.py <target_ip> [threads]")
        sys.exit(1)

    target = sys.argv[1]
    num_threads = int(sys.argv[2]) if len(sys.argv) > 2 else None

    result = recon_scan(target, threads=num_threads)
    print(f"\n[*] Scan completed: {len(result['open_ports'])} open ports")
    print(f"Open ports: {result['open_ports']}")
