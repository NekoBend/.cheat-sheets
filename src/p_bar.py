"""
Python Parallel Processing & Progress Bar Best Practices Reference.
This file is designed as a "Copy-Paste Snippet Collection".
Each function is self-contained with necessary imports.

Usage:
    Copy the function you need (e.g., `run_multithread_basic`) into your script.
    Replace `process_item` with your actual logic.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

# ==============================================================================
# Domain Objects (Example)
# ==============================================================================


@dataclass(frozen=True)
class ProcessResult:
    """Standardized result object to handle successes and failures gracefully."""

    success: bool
    data: int | str | None = None
    error: str | None = None


Item = int  # Type alias for input data


def process_item_io_bound(item: Item) -> ProcessResult:
    """
    Simulation of an IO-bound task (e.g., API request, DB query).
    Wait time: 0.1s
    """
    import random

    time.sleep(0.1)
    if random.random() < 0.1:  # 10% failure chance
        return ProcessResult(False, error=f"Connection timeout on {item}")
    return ProcessResult(True, data=f"Response from {item}")


def process_item_cpu_bound(item: Item) -> ProcessResult:
    """
    Simulation of a CPU-bound task (e.g., Image processing, Calculation).
    Wait time: 0.1s (busy_wait simulation)
    """
    # In real CPU bound, this would be heavy calculation
    import random

    time.sleep(0.1)
    if random.random() < 0.1:
        return ProcessResult(False, error=f"Calculation error on {item}")
    return ProcessResult(True, data=item * item)


# ==============================================================================
# 0. Sequential (For Debugging & Simple Tasks)
# ==============================================================================


def run_sequential_tqdm(items: list[Item]) -> list[ProcessResult]:
    """
    [Best for] Simple scripts, debugging, or when order matters strictly.
    [UI] Standard tqdm progress bar.
    """
    from tqdm import tqdm

    results = []
    # print("--- Sequential (tqdm) ---")
    for item in tqdm(items, desc="Seq Processing"):
        results.append(process_item_io_bound(item))
    return results


def run_sequential_rich(items: list[Item]) -> list[ProcessResult]:
    """
    [Best for] CLI applications where aesthetics matter.
    [UI] Beautiful Rich progress bar.
    """
    from rich.progress import track

    results = []
    # print("--- Sequential (rich) ---")
    for item in track(items, description="[green]Seq Processing..."):
        results.append(process_item_io_bound(item))
    return results


# ==============================================================================
# 1. Multi-Threading (Best for IO-Bound)
# ==============================================================================


def run_multithread_fast(
    items: list[Item], max_workers: int = 8
) -> list[ProcessResult]:
    """
    [Best for] Network/Disk IO tasks. The Easiest & Fastest way to write.
    [Note] `thread_map` preserves the order of results (like map).
    """
    from tqdm.contrib.concurrent import thread_map

    # print("--- Threading (tqdm.contrib.thread_map) ---")
    # This acts exactly like map(), but multithreaded + progress bar
    results = thread_map(
        process_item_io_bound,
        items,
        max_workers=max_workers,
        desc="IO Threads",
    )
    return results  # type: ignore


def run_multithread_manual(
    items: list[Item], max_workers: int = 8
) -> list[ProcessResult]:
    """
    [Best for] Complex IO tasks needing error handling or early-stopping.
    [Note] `as_completed` yields results as soon as they finish (Order NOT guaranteed).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from tqdm import tqdm

    # print("--- Threading (Executor + as_completed) ---")
    results: list[ProcessResult] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {
            executor.submit(process_item_io_bound, item): item for item in items
        }

        # Process as they complete
        for future in tqdm(
            as_completed(future_to_item), total=len(items), desc="IO Threads (Manual)"
        ):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # Critical error handling that didn't get caught inside process_item
                print(f"Critical Worker Error: {e}")

    return results


# ==============================================================================
# 2. Multi-Processing (Best for CPU-Bound)
# ==============================================================================


def run_multiprocess_fast(
    items: list[Item], max_workers: int = 4
) -> list[ProcessResult]:
    """
    [Best for] Heavy CPU calculations. The Easiest way to write.
    [Note] Uses `process_map` (wrapper around ProcessPoolExecutor).
    """
    from tqdm.contrib.concurrent import process_map

    # print("--- Multiprocessing (tqdm.contrib.process_map) ---")
    results = process_map(
        process_item_cpu_bound,
        items,
        max_workers=max_workers,
        desc="CPU Processes",
        chunksize=1,  # Adjust chunksize for performance
    )
    return results  # type: ignore


def run_mpire_dashboard(items: list[Item], max_workers: int = 4) -> list[ProcessResult]:
    """
    [Best for] Heavy CPU tasks requiring maximum performance & detailed UI.
    [Requires] `pip install mpire`
    [Note] Faster than standard multiprocessing (uses shared memory).
    """
    try:
        from mpire import WorkerPool
    except ImportError:
        print("Skipping: mpire not installed. (pip install mpire)")
        return []

    # print("--- MPIRE (Optimized Multiprocessing) ---")
    # Note: On Windows, mpire usually needs main guard, but inside a function often works if spawned correctly.
    # 'enable_slurm=False' prevents some cluster checks generally.
    with WorkerPool(n_jobs=max_workers) as pool:
        results = pool.map(
            process_item_cpu_bound,
            items,
            progress_bar=True,
            progress_bar_options={"desc": "MPIRE CPU"},
        )
    return results  # type: ignore


def run_multiprocess_rich_ui(
    items: list[Item], max_workers: int = 4
) -> list[ProcessResult]:
    """
    [Best for] CPU-Bound tasks where you want a Beautiful UI (Rich).
    [Note] Combining ProcessPoolExecutor + Rich requires manual updates via Context Manager.
    """
    from concurrent.futures import ProcessPoolExecutor, as_completed

    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )

    results = []
    # print("--- Multiprocessing (Rich UI) ---")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task_id = progress.add_task("CPU Rich Worker", total=len(items))

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_item_cpu_bound, item): item for item in items
            }

            for future in as_completed(futures):
                results.append(future.result())
                progress.advance(task_id)

    return results


# ==============================================================================
# 3. AsyncIO (Best for Massive Web Requests)
# ==============================================================================


async def run_async_massive_io(items: list[Item]) -> list[ProcessResult]:
    """
    [Best for] Thousands of API requests where threading overhead is too high.
    [Requires] Async version of the processing function.
    """
    import asyncio

    from tqdm.asyncio import tqdm

    # Dummy async function mimicking an HTTP request
    async def async_fetch(item: Item) -> ProcessResult:
        import random

        await asyncio.sleep(0.1)  # Non-blocking sleep
        if random.random() < 0.1:
            return ProcessResult(False, error=f"Timeout {item}")
        return ProcessResult(True, data=f"Async Data {item}")

    # print("--- AsyncIO (tqdm.asyncio) ---")
    # gather runs them concurrently
    results = await tqdm.gather(
        *[async_fetch(item) for item in items], desc="AsyncIO Requests"
    )
    return results


# ==============================================================================
# Main Execution Demo
# ==============================================================================


def main():
    import logging

    # Setup simple logging to see what's happening if needed
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    items = list(range(50))
    print(f"\nProcessing {len(items)} items using various best practices...\n")

    # 1. Sequential
    run_sequential_tqdm(items)

    # 2. IO Bound Best Practices
    run_multithread_fast(items)  # Recommended for simplicity
    run_multithread_manual(items)  # Recommended for control

    # 3. CPU Bound Best Practices
    # Guard for Windows multiprocessing
    if __name__ == "__main__":
        run_multiprocess_fast(items)  # Recommended for simplicity
        run_multiprocess_rich_ui(items)  # Recommended for visuals
        run_mpire_dashboard(items)  # Recommended for speed

    # 4. Async
    import asyncio

    asyncio.run(run_async_massive_io(items))

    print("\nAll Demos Completed Successfully.")


if __name__ == "__main__":
    main()
