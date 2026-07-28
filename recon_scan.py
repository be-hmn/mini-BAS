import socket
import threading
from concurrent.futures import ThreadPoolExecutor

def recon_scan(target_ip, start_port=1, end_port=1023, threads=4, timeout=0.5):
    """
    Multithreaded TCP connect scan - well-known ports (0-1023)
    """
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
                    print(f"[+] {target_ip}:{port} OPEN")
        except:
            pass

    print(f"[*] Scanning {target_ip} ports {start_port}-{end_port} ({threads} threads)...")
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
    num_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    result = recon_scan(target, threads=num_threads)
    print(f"\n[*] Scan completed: {len(result['open_ports'])} open ports")
    print(f"Open ports: {result['open_ports']}")
