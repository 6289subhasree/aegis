"""Synthetic Surge Queue Simulation (Poster Section 12).

Reproduces:
    EARLY EVIDENCE · SYNTHETIC SURGE QUEUE (MEAN CRITICAL WAIT, ONE OFFICER)
    One officer, mean 0.78 min per report, 15% critical, 400 reports, 200 runs.
    Demonstrates why queue discipline (Severity-First vs FIFO) matters under disaster surges:
        Load 0.85: FIFO 4.1 min vs Severity-first 0.8 min (-81%)
        Load 1.00: FIFO 11.0 min vs Severity-first 0.9 min (-92%)
        Load 1.30: FIFO 37.8 min vs Severity-first 1.0 min (-97%)
"""

import heapq
import random
from dataclasses import dataclass, field


@dataclass(order=True)
class QueueItem:
    priority: tuple
    arrival_time: float = field(compare=False)
    is_critical: bool = field(compare=False)
    service_time: float = field(compare=False)


def run_single_simulation(
    num_reports: int = 400,
    mean_service_min: float = 0.78,
    pct_critical: float = 0.15,
    offered_load: float = 1.0,
    severity_first: bool = True,
    seed: int | None = None,
) -> float:
    """Returns mean wait time (in minutes) for CRITICAL reports under M/M/1 queueing."""
    if seed is not None:
        random.seed(seed)

    arrival_rate = offered_load / mean_service_min

    # Generate arrivals (Poisson process)
    arrivals = []
    current_time = 0.0
    for _ in range(num_reports):
        current_time += random.expovariate(arrival_rate)
        is_crit = random.random() < pct_critical
        service_time = random.expovariate(1.0 / mean_service_min)
        arrivals.append((current_time, is_crit, service_time))

    # Event-driven discrete event queue simulation
    queue: list[QueueItem] = []
    clock = 0.0
    critical_waits: list[float] = []

    arr_idx = 0
    total_arrivals = len(arrivals)

    while arr_idx < total_arrivals or queue:
        # If server is idle, advance clock to the next arrival time
        if not queue and clock < arrivals[arr_idx][0]:
            clock = arrivals[arr_idx][0]

        # Enqueue all reports that have already arrived by the current clock
        while arr_idx < total_arrivals and arrivals[arr_idx][0] <= clock:
            arr_t, is_c, s_t = arrivals[arr_idx]
            # Severity-first: critical items get priority 0 (served first), tie-broken by arrival time
            # FIFO: arrival time alone determines service order
            prio = (0 if is_c else 1, arr_t) if severity_first else (arr_t, arr_t)
            heapq.heappush(
                queue,
                QueueItem(priority=prio, arrival_time=arr_t, is_critical=is_c, service_time=s_t),
            )
            arr_idx += 1

        # Serve the highest-priority arrived report
        if queue:
            item = heapq.heappop(queue)
            wait = clock - item.arrival_time
            if item.is_critical:
                critical_waits.append(wait)
            clock += item.service_time

    return sum(critical_waits) / len(critical_waits) if critical_waits else 0.0


def benchmark_surge_queue(runs: int = 200, seed: int = 42) -> dict:
    loads = [0.85, 1.00, 1.30]
    print("=" * 72)
    print("DISASTERSIGNAL · SYNTHETIC SURGE QUEUE EVALUATION (Poster Section 12)")
    print("One officer, mean 0.78 min/report, 15% critical, 400 reports, 200 runs")
    print("=" * 72)
    print(f"{'Offered Load':<14} | {'FIFO Mean Wait':<16} | {'Severity-First':<16} | {'Improvement':<12}")
    print("-" * 72)

    results = {}
    for load in loads:
        fifo_waits = [
            run_single_simulation(offered_load=load, severity_first=False, seed=seed + i)
            for i in range(runs)
        ]
        sev_waits = [
            run_single_simulation(offered_load=load, severity_first=True, seed=seed + i)
            for i in range(runs)
        ]

        mean_fifo = sum(fifo_waits) / len(fifo_waits)
        mean_sev = sum(sev_waits) / len(sev_waits)
        pct_imp = (mean_fifo - mean_sev) / mean_fifo * 100.0

        print(f"Load {load:<9.2f} | {mean_fifo:>6.1f} min        | {mean_sev:>6.1f} min        | -{pct_imp:>4.0f}%")
        results[load] = {
            "fifo": round(mean_fifo, 1),
            "severity_first": round(mean_sev, 1),
            "improvement": round(pct_imp, 0),
        }

    print("=" * 72)
    return results


if __name__ == "__main__":
    benchmark_surge_queue()
