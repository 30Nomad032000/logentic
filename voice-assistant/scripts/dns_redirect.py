#!/usr/bin/env python3
"""
Local DNS server that redirects EdgeX/XiaoZhi OTA domains to our local server.
Run this so the EdgeX device connects to our FastAPI backend instead of the cloud.

Usage:
    python scripts/dns_redirect.py

Then configure your router's DHCP to use this PC (192.168.1.101) as DNS,
or manually set the EdgeX device's DNS to this PC.
"""

import socket
import struct
import threading
import sys

# Our server IP
LOCAL_SERVER_IP = "192.168.1.101"

# Domains to redirect to our server
REDIRECT_DOMAINS = {
    "api.edgex.cn",
    "edgex.cn",
    "api.edgex.ai",
    "edgex.ai",
    "api.tenclass.net",  # XiaoZhi default OTA
    "xiaozhi.me",
    "api.xiaozhi.me",
}

# Upstream DNS for everything else
UPSTREAM_DNS = "8.8.8.8"


def build_response(data, redirect_ip):
    """Build a DNS response redirecting to our IP."""
    # Parse the query
    transaction_id = data[:2]
    flags = b'\x81\x80'  # Standard response, no error
    questions = data[4:6]
    answers = b'\x00\x01'  # 1 answer
    authority = b'\x00\x00'
    additional = b'\x00\x00'

    # Find the question section
    question_end = 12
    while data[question_end] != 0:
        question_end += data[question_end] + 1
    question_end += 5  # null byte + qtype(2) + qclass(2)

    question_section = data[12:question_end]

    # Build answer: pointer to name + type A + class IN + TTL + IP
    answer = b'\xc0\x0c'  # Pointer to name in question
    answer += b'\x00\x01'  # Type A
    answer += b'\x00\x01'  # Class IN
    answer += struct.pack('>I', 60)  # TTL 60 seconds
    answer += b'\x00\x04'  # Data length 4
    answer += socket.inet_aton(redirect_ip)

    return transaction_id + flags + questions + answers + authority + additional + question_section + answer


def extract_domain(data):
    """Extract domain name from DNS query."""
    parts = []
    idx = 12
    while data[idx] != 0:
        length = data[idx]
        parts.append(data[idx + 1:idx + 1 + length].decode('ascii', errors='ignore'))
        idx += length + 1
    return '.'.join(parts)


def handle_query(data, addr, sock):
    """Handle a DNS query."""
    try:
        domain = extract_domain(data)

        if domain.lower() in REDIRECT_DOMAINS:
            print(f"[REDIRECT] {domain} -> {LOCAL_SERVER_IP} (from {addr[0]})")
            response = build_response(data, LOCAL_SERVER_IP)
            sock.sendto(response, addr)
        else:
            # Forward to upstream DNS
            upstream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            upstream.settimeout(3)
            upstream.sendto(data, (UPSTREAM_DNS, 53))
            try:
                response, _ = upstream.recvfrom(4096)
                sock.sendto(response, addr)
            except socket.timeout:
                print(f"[TIMEOUT] Upstream DNS timeout for {domain}")
            finally:
                upstream.close()
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    print(f"Starting DNS redirect server on port 53")
    print(f"Redirecting EdgeX/XiaoZhi domains to {LOCAL_SERVER_IP}")
    print(f"Domains: {', '.join(sorted(REDIRECT_DOMAINS))}")
    print(f"Upstream DNS: {UPSTREAM_DNS}")
    print()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('0.0.0.0', 53))
    except PermissionError:
        print("ERROR: Need admin privileges to bind port 53.")
        print("Run this script as Administrator.")
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: Cannot bind port 53: {e}")
        print("Another DNS service may be running. Try stopping it first.")
        sys.exit(1)

    print("DNS server running. Press Ctrl+C to stop.\n")

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            thread = threading.Thread(target=handle_query, args=(data, addr, sock))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nStopping DNS server.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
