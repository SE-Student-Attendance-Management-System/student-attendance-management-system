"""
Reproducible Benchmark: Login Page Performance (ST-01-01 / AC-6)
Measures the response time for requesting the login interface against the
SRS requirement of < 3.0 seconds under normal operating conditions.
"""

import os
import platform
import statistics
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.test_settings")

import django

django.setup()

from django.conf import settings
from django.test import Client
from django.urls import reverse


def run_benchmark(iterations: int = 20):
    client = Client(SERVER_NAME="localhost")
    login_url = reverse("login")

    # Warm-up request
    warmup_res = client.get(login_url)
    assert warmup_res.status_code == 200, f"Expected 200, got {warmup_res.status_code}"

    latencies_ms = []
    for _ in range(iterations):
        start = time.perf_counter()
        res = client.get(login_url)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert res.status_code == 200
        latencies_ms.append(elapsed_ms)

    mean_ms = statistics.mean(latencies_ms)
    median_ms = statistics.median(latencies_ms)
    min_ms = min(latencies_ms)
    max_ms = max(latencies_ms)
    stdev_ms = statistics.stdev(latencies_ms) if len(latencies_ms) > 1 else 0.0

    print("=" * 60)
    print("SAMS LOGIN PAGE PERFORMANCE BENCHMARK (ST-01-01 / AC-6)")
    print("=" * 60)
    print("ENVIRONMENT DETAILS:")
    print(f"  OS / Platform:      {platform.platform()}")
    print(f"  Processor:          {platform.processor()}")
    print(f"  Python Version:     {sys.version.split()[0]}")
    print(f"  Django Version:     {django.get_version()}")
    print(f"  Database Engine:    {settings.DATABASES['default']['ENGINE']}")
    print("-" * 60)
    print("MEASUREMENT RESULTS:")
    print(f"  Target URL:         {login_url}")
    print(f"  Sample Size:        {iterations} requests")
    print(f"  Min Latency:        {min_ms:.2f} ms")
    print(f"  Max Latency:        {max_ms:.2f} ms")
    print(f"  Median Latency:     {median_ms:.2f} ms")
    print(f"  Mean Latency:       {mean_ms:.2f} ms")
    print(f"  Std Deviation:      {stdev_ms:.2f} ms")
    print(f"  SRS Target:         < 3000.00 ms (3.0 seconds)")
    print("-" * 60)
    passed = max_ms < 3000.0
    print(f"  Status:             {'PASS [Compliant with SRS & ST-01-01]' if passed else 'FAIL'}")
    print("=" * 60)
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": sys.version.split()[0],
        "django_version": django.get_version(),
        "db_engine": settings.DATABASES["default"]["ENGINE"],
        "iterations": iterations,
        "min_ms": min_ms,
        "max_ms": max_ms,
        "median_ms": median_ms,
        "mean_ms": mean_ms,
        "stdev_ms": stdev_ms,
        "passed": passed,
    }


if __name__ == "__main__":
    run_benchmark()
