import subprocess
import re
import sys


def perform_traceroute(host, max_hops=30, timeout=2):
    result = []

    for ttl in range(1, max_hops + 1):
        if sys.platform == "win32":
            cmd = ["tracert", "-h", str(ttl), "-w", str(timeout * 1000), host]
        else:
            cmd = ["traceroute", "-m", str(ttl), "-w", str(timeout), host]

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        except Exception as e:
            output = str(e)

        ip_pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        match = re.search(ip_pattern, output)

        if match:
            ip = match.group()
            result.append({"hop": ttl, "ip": ip, "rtt": None})
        else:
            result.append({"hop": ttl, "ip": None, "rtt": None})

        if "Destination host unreachable" in output or "Request timed out" in output:
            break

    return result


def format_result(hops):
    for hop in hops:
        hop_number = hop["hop"]
        ip_address = hop["ip"] or "*"
        print(f"{hop_number}: {ip_address}")


def main():
    host = "ya.ru"
    print(f"🔍 Трассировка до {host}...")
    route = perform_traceroute(host)

    print("\n📊 Результаты трассировки:")
    format_result(route)


if __name__ == "__main__":
    main()