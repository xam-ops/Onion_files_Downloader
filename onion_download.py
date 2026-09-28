#!/usr/bin/env python3

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlparse

import requests


TOR_SOCKS_PORT = 19050
TOR_STARTUP_TIMEOUT = 120


def wait_for_port(host, port, timeout):
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1)

    return False


def start_tor():
    tor_path = shutil.which("tor")

    if not tor_path:
        sys.exit("Tor is not installed or is not in PATH.")

    tor_data_dir = tempfile.mkdtemp(prefix="python-tor-")

    tor_command = [
        tor_path,
        "--SocksPort", str(TOR_SOCKS_PORT),
        "--DataDirectory", tor_data_dir,
        "--Log", "notice stdout",
    ]

    process = subprocess.Popen(
        tor_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print("Starting Tor...")

    if not wait_for_port("127.0.0.1", TOR_SOCKS_PORT, TOR_STARTUP_TIMEOUT):
        process.terminate()
        shutil.rmtree(tor_data_dir, ignore_errors=True)
        sys.exit("Tor did not start within the timeout period.")

    print("Tor SOCKS proxy is ready.")
    return process, tor_data_dir


def valid_onion_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    if not parsed.hostname or not parsed.hostname.endswith(".onion"):
        return False

    return True


def download_file(url, output_path):
    proxy = f"socks5h://127.0.0.1:{TOR_SOCKS_PORT}"

    proxies = {
        "http": proxy,
        "https": proxy,
    }

    print(f"Downloading: {url}")
    print(f"Saving to:   {output_path}")

    with requests.get(
        url,
        proxies=proxies,
        stream=True,
        timeout=(30, 120),
        headers={
            "User-Agent": "onion-downloader/1.0",
        },
    ) as response:
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue

                file.write(chunk)
                downloaded += len(chunk)

                if total_size:
                    percent = downloaded * 100 / total_size
                    print(
                        f"\r{downloaded / 1024 / 1024:.2f} MB "
                        f"/ {total_size / 1024 / 1024:.2f} MB "
                        f"({percent:.1f}%)",
                        end="",
                        flush=True,
                    )
                else:
                    print(
                        f"\rDownloaded {downloaded / 1024 / 1024:.2f} MB",
                        end="",
                        flush=True,
                    )

    print("\nDownload complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Download a file from a Tor onion service."
    )
    parser.add_argument("url", help="HTTP or HTTPS .onion URL")
    parser.add_argument(
        "-o",
        "--output",
        help="Output filename; defaults to the URL filename",
    )

    args = parser.parse_args()

    if not valid_onion_url(args.url):
        sys.exit("Please provide a valid HTTP/HTTPS .onion URL.")

    output_path = args.output

    if not output_path:
        filename = os.path.basename(urlparse(args.url).path)
        output_path = filename or "onion-download"

    tor_process = None
    tor_data_dir = None

    try:
        tor_process, tor_data_dir = start_tor()
        download_file(args.url, output_path)

    except requests.exceptions.RequestException as error:
        sys.exit(f"\nDownload failed: {error}")

    except KeyboardInterrupt:
        print("\nInterrupted.")

    finally:
        if tor_process and tor_process.poll() is None:
            tor_process.send_signal(signal.SIGTERM)
            try:
                tor_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                tor_process.kill()

        if tor_data_dir:
            shutil.rmtree(tor_data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
