"""Generate a steady CUDA load for the Week 4 GPU sharing exercises."""

import os
import signal
import time

import torch


RUNNING = True


def stop(_signum, _frame):
    global RUNNING
    RUNNING = False


def main():
    duration = int(os.getenv("DURATION_SECONDS", "1800"))
    matrix_size = int(os.getenv("MATRIX_SIZE", "2048"))
    report_interval = int(os.getenv("REPORT_INTERVAL_SECONDS", "10"))

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available in this container")

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    device = torch.device("cuda:0")
    properties = torch.cuda.get_device_properties(device)
    print(
        f"device={properties.name} cuda={torch.version.cuda} "
        f"memory_mib={properties.total_memory // 1024 // 1024}",
        flush=True,
    )
    print(
        f"duration_seconds={duration} matrix_size={matrix_size}",
        flush=True,
    )

    left = torch.randn((matrix_size, matrix_size), device=device)
    right = torch.randn((matrix_size, matrix_size), device=device)
    started = time.monotonic()
    last_report = started
    iterations = 0

    while RUNNING and time.monotonic() - started < duration:
        result = torch.matmul(left, right)
        left, right = right, result / max(matrix_size, 1)
        iterations += 1

        now = time.monotonic()
        if now - last_report >= report_interval:
            torch.cuda.synchronize(device)
            print(
                f"elapsed_seconds={now - started:.1f} iterations={iterations}",
                flush=True,
            )
            last_report = now

    torch.cuda.synchronize(device)
    print(f"completed iterations={iterations}", flush=True)


if __name__ == "__main__":
    main()
