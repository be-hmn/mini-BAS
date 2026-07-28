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
BANNER_SIZE = 256
HTTP_PROBE_PORTS = {80, 443, 8000, 8080}


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


def _grab_banner(sock: socket.socket, port: int) -> str:
    """열린 소켓에서 서비스 배너를 읽는다. 얻지 못하면 빈 문자열."""
    try:
        data = sock.recv(BANNER_SIZE)
    except OSError:
        data = b""

    if not data and port in HTTP_PROBE_PORTS:
        try:
            sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
            data = sock.recv(BANNER_SIZE)
        except OSError:
            data = b""

    return data.decode("utf-8", errors="ignore").strip()


def recon_scan(target_ip, start_port=1, end_port=1023, threads=None, timeout=0.5):
    """
    Multithreaded TCP connect scan - well-known ports (0-1023)
    각 열린 포트에서 서비스 배너를 함께 수집한다 (얻지 못하면 빈 문자열).
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

            if result == 0:
                banner = _grab_banner(s, port)
                with lock:
                    open_ports.append({"port": port, "banner": banner})
                logger.info("%s:%d OPEN (banner=%r)", target_ip, port, banner)
            s.close()
        except OSError:
            pass

    logger.info("Scanning %s ports %d-%d (%d threads)...", target_ip, start_port, end_port, threads)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(scan_port, range(start_port, end_port + 1))

    return {
        "target": target_ip,
        "open_ports": sorted(open_ports, key=lambda p: p["port"]),
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
    for p in result["open_ports"]:
        print(f"  {p['port']}\t{p['banner'] or '(no banner)'}")
