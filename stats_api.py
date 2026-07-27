"""
Ultra Gaming VPN — Stats API
Lightweight HTTP server on 127.0.0.1:8888
Endpoints:
  GET /stats  → JSON snapshot
  GET /stream → SSE stream (event every 2s)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, time, os, threading

# ── Sampler ──────────────────────────────────────────────────────────────────

_state = {
    "cpu_idle_prev": None,
    "cpu_total_prev": None,
    "net_rx_prev": None,
    "net_tx_prev": None,
    "net_time_prev": None,
    "lock": threading.Lock(),
}


def _read_cpu_raw():
    with open("/proc/stat") as f:
        parts = f.readline().split()
    vals = list(map(int, parts[1:]))
    idle  = vals[3] + vals[4]   # idle + iowait
    total = sum(vals)
    return idle, total


def _read_mem():
    m = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, v = line.split(":", 1)
            m[k.strip()] = int(v.strip().split()[0])
    total     = m.get("MemTotal", 0)
    available = m.get("MemAvailable", m.get("MemFree", 0))
    used      = total - available
    return {
        "total_mb":  round(total     / 1024, 1),
        "used_mb":   round(used      / 1024, 1),
        "free_mb":   round(available / 1024, 1),
        "percent":   round(used / max(total, 1) * 100, 1),
    }


def _read_net_raw():
    rx = tx = 0
    with open("/proc/net/dev") as f:
        for line in f.readlines()[2:]:
            parts = line.split()
            iface = parts[0].rstrip(":")
            if iface == "lo":
                continue
            rx += int(parts[1])
            tx += int(parts[9])
    return rx, tx


def _read_uptime():
    with open("/proc/uptime") as f:
        secs = float(f.read().split()[0])
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    return f"{h}h {m}m {s}s", int(secs)


def sample():
    with _state["lock"]:
        now = time.time()

        # ── CPU ──
        idle, total = _read_cpu_raw()
        if _state["cpu_idle_prev"] is not None:
            d_idle  = idle  - _state["cpu_idle_prev"]
            d_total = total - _state["cpu_total_prev"]
            cpu_pct = round((1 - d_idle / max(d_total, 1)) * 100, 1)
        else:
            cpu_pct = 0.0
        _state["cpu_idle_prev"]  = idle
        _state["cpu_total_prev"] = total

        # ── MEM ──
        mem = _read_mem()

        # ── NET ──
        rx, tx = _read_net_raw()
        if _state["net_rx_prev"] is not None:
            dt = now - _state["net_time_prev"]
            rx_speed = round((rx - _state["net_rx_prev"]) / max(dt, 0.001) / 1024, 1)
            tx_speed = round((tx - _state["net_tx_prev"]) / max(dt, 0.001) / 1024, 1)
        else:
            rx_speed = tx_speed = 0.0
        _state["net_rx_prev"]   = rx
        _state["net_tx_prev"]   = tx
        _state["net_time_prev"] = now

        uptime_str, uptime_sec = _read_uptime()

        return {
            "cpu":     cpu_pct,
            "memory":  mem,
            "network": {
                "rx_total_mb": round(rx / 1048576, 2),
                "tx_total_mb": round(tx / 1048576, 2),
                "rx_speed_kb": rx_speed,
                "tx_speed_kb": tx_speed,
            },
            "uptime":     uptime_str,
            "uptime_sec": uptime_sec,
            "timestamp":  int(now),
        }


# ── Handler ──────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silent

    def do_GET(self):
        if self.path in ("/stats", "/"):
            data = sample()
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                while True:
                    data = sample()
                    msg  = f"data: {json.dumps(data)}\n\n"
                    self.wfile.write(msg.encode())
                    self.wfile.flush()
                    time.sleep(2)
            except (BrokenPipeError, ConnectionResetError):
                pass

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8888), Handler)
    server.serve_forever()
