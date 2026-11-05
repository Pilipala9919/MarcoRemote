"""Read-only G0 inventory. No subnet scan, input injection or device changes.

Logs are local/private by default; redact addresses and service names before sharing.
"""
import argparse
import datetime
import json
from pathlib import Path
import socket
import subprocess
import time


def tcp_probe(host, port, source, timeout=3):
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout, (source, 0)):
            result = {"result": "tcp_open"}
    except OSError as error:
        result = {"result": type(error).__name__, "errno": error.errno}
    return dict(result, port=port, elapsed_ms=round((time.monotonic()-started)*1000, 1))


def discover(interface, duration):
    from zeroconf import Zeroconf, ServiceBrowser, ServiceListener, IPVersion

    class Listener(ServiceListener):
        def __init__(self):
            self.names = set()

        def add_service(self, zc, type_, name):
            self.names.add(name)

        def update_service(self, zc, type_, name):
            self.names.add(name)

        def remove_service(self, zc, type_, name):
            pass  # retain observations, including services that disappear

    listener = Listener()
    service = "_androidtvremote2._tcp.local."
    zc = Zeroconf(interfaces=[interface], ip_version=IPVersion.V4Only)
    browser = ServiceBrowser(zc, service, listener)
    try:
        time.sleep(duration)
        browser.cancel()  # stop callbacks before taking snapshot
        records = []
        for name in sorted(listener.names):
            info = zc.get_service_info(service, name, timeout=2000)
            records.append({"name": name, "addresses": info.parsed_addresses() if info else [],
                            "port": info.port if info else None})
        return {"result": "completed", "duration_seconds": duration, "records": records}
    finally:
        zc.close()


def adb_inventory(adb, serial):
    queries = {
        "model": ["getprop", "ro.product.model"],
        "android": ["getprop", "ro.build.version.release"],
        "sdk": ["getprop", "ro.build.version.sdk"],
        "firmware": ["getprop", "ro.build.display.id"],
        "remote_packages": ["pm", "list", "packages", "remote"],
        "google_remote_including_uninstalled": ["pm", "list", "packages", "-u", "com.google.android.tv.remote"],
        "google_remote_path": ["pm", "path", "com.google.android.tv.remote.service"],
        "listeners": ["cat", "/proc/net/tcp"],
        "listeners6": ["cat", "/proc/net/tcp6"],
    }
    results = {}
    for name, args in queries.items():
        try:
            run = subprocess.run([adb, "-s", serial, "shell", *args], capture_output=True,
                                 text=True, timeout=10)
            results[name] = {"exit": run.returncode, "stdout": run.stdout.strip(),
                             "stderr": run.stderr.strip()}
        except subprocess.TimeoutExpired:
            results[name] = {"error": "timeout"}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--interface", required=True, help="Physical LAN IPv4")
    parser.add_argument("--adb")
    parser.add_argument("--serial")
    parser.add_argument("--seconds", type=int, default=15, choices=range(1, 61))
    parser.add_argument("--output", type=Path, default=Path("private/g0-probe.json"))
    args = parser.parse_args()
    if bool(args.adb) != bool(args.serial):
        parser.error("--adb and --serial must be supplied together")
    report = {"schema": 1, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "host": args.host, "interface": args.interface, "tcp": []}
    if args.adb:
        report["adb"] = adb_inventory(args.adb, args.serial)
    for attempt in range(3):
        for port in (6466, 6467):
            report["tcp"].append(dict(tcp_probe(args.host, port, args.interface), attempt=attempt+1))
        if attempt < 2:
            time.sleep(1)
    try:
        report["discovery"] = discover(args.interface, args.seconds)
    except Exception as error:
        report["discovery"] = {"result": "error", "error_type": type(error).__name__}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"log": str(args.output), "tcp": report["tcp"],
                      "discovery_status": report["discovery"]["result"],
                      "discovered_count": len(report["discovery"].get("records", []))}))


if __name__ == "__main__":
    main()
