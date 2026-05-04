#!/usr/bin/env python3
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    task_id: str
    arrival: int
    duration: int
    core: int | None = None
    start: int | None = None
    end: int | None = None

    @property
    def wait_time(self) -> int:
        if self.start is None:
            return 0
        return self.start - self.arrival

    @property
    def turnaround_time(self) -> int:
        if self.end is None:
            return 0
        return self.end - self.arrival


@dataclass
class Result:
    tasks: list[Task]
    total_time: int
    throughput: float
    core_busy: list[int]
    core_utilization: list[float]
    timeline: list[list[tuple[str, int, int]]]


def load_tasks_from_file(filename: str) -> tuple[int, list[Task]]:
    lines = [line.strip() for line in Path(filename).read_text(encoding="utf-8").splitlines() if line.strip()]

    if len(lines) < 2:
        raise ValueError("Input file must have at least 2 lines.")

    cores = int(lines[0])
    task_count = int(lines[1])

    if cores <= 0:
        raise ValueError("Number of cores must be positive.")
    if task_count < 0:
        raise ValueError("Task count cannot be negative.")
    if len(lines) != task_count + 2:
        raise ValueError("Task count does not match the number of task lines.")

    tasks = []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f"Invalid task line: {line}")

        task_id = parts[0]
        arrival = int(parts[1])
        duration = int(parts[2])

        if arrival < 0:
            raise ValueError(f"Arrival time must be non-negative: {line}")
        if duration <= 0:
            raise ValueError(f"Duration must be positive: {line}")

        tasks.append(Task(task_id, arrival, duration))

    return cores, tasks


def simulate(base_tasks: list[Task], cores: int) -> Result:
    tasks = [Task(t.task_id, t.arrival, t.duration) for t in base_tasks]
    tasks.sort(key=lambda t: (t.arrival, t.task_id))

    ready = deque()
    running: list[tuple[Task, int] | None] = [None] * cores
    timeline: list[list[tuple[str, int, int]]] = [[] for _ in range(cores)]
    core_busy = [0] * cores

    time = 0
    next_task_index = 0
    completed = 0
    total_tasks = len(tasks)

    while completed < total_tasks:
        if (
            not ready
            and all(slot is None for slot in running)
            and next_task_index < total_tasks
            and time < tasks[next_task_index].arrival
        ):
            time = tasks[next_task_index].arrival

        for core_index in range(cores):
            slot = running[core_index]
            if slot is not None and slot[1] == time:
                running[core_index] = None
                completed += 1

        while next_task_index < total_tasks and tasks[next_task_index].arrival == time:
            ready.append(tasks[next_task_index])
            next_task_index += 1

        for core_index in range(cores):
            if running[core_index] is None and ready:
                task = ready.popleft()
                task.core = core_index
                task.start = time
                task.end = time + task.duration
                running[core_index] = (task, task.end)
                timeline[core_index].append((task.task_id, task.start, task.end))
                core_busy[core_index] += task.duration

        if completed == total_tasks:
            break

        next_times = []

        for slot in running:
            if slot is not None:
                next_times.append(slot[1])

        if next_task_index < total_tasks:
            next_times.append(tasks[next_task_index].arrival)

        if not next_times:
            break

        time = min(next_times)

    total_time = max(task.end for task in tasks if task.end is not None)
    throughput = total_tasks / total_time if total_time else 0.0
    core_utilization = [(busy / total_time) * 100 if total_time else 0.0 for busy in core_busy]

    tasks.sort(key=lambda t: t.task_id)
    return Result(tasks, total_time, throughput, core_busy, core_utilization, timeline)


def write_lines(filename: str, lines: list[str]) -> None:
    Path(filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trace_lines(result: Result) -> list[str]:
    events: list[tuple[int, str]] = []

    for core_index, entries in enumerate(result.timeline):
        for task_id, start, end in entries:
            events.append((start, f"t={start}: CORE {core_index} START {task_id}"))
            events.append((end, f"t={end}: CORE {core_index} END   {task_id}"))

    events.sort(key=lambda item: (item[0], item[1]))
    return [line for _, line in events]


def write_task_log(tasks: list[Task], filename: str) -> None:
    lines = []
    lines.append("TASK  ARRIVAL  DURATION  CORE  START  END  WAIT  TURNAROUND")
    for task in tasks:
        lines.append(
            f"{task.task_id:<5} "
            f"{task.arrival:<8} "
            f"{task.duration:<9} "
            f"{task.core:<5} "
            f"{task.start:<6} "
            f"{task.end:<4} "
            f"{task.wait_time:<5} "
            f"{task.turnaround_time}"
        )
    write_lines(filename, lines)


def write_core_log(result: Result, filename: str) -> None:
    lines = []

    for core_index, entries in enumerate(result.timeline):
        lines.append(f"CORE {core_index}")
        lines.append(f"busy_time={result.core_busy[core_index]}")
        lines.append(f"utilization={result.core_utilization[core_index]:.2f}%")

        if not entries:
            lines.append("timeline=idle")
        else:
            schedule = " -> ".join(f"{task}[{start}-{end}]" for task, start, end in entries)
            lines.append(f"timeline={schedule}")

        lines.append("")

    write_lines(filename, lines)


def write_sim_stats(filename: str, multicore: Result, singlecore: Result, cores: int) -> None:
    lines = []
    lines.append(f"cores={cores}")
    lines.append(f"tasks_completed={len(multicore.tasks)}")
    lines.append(f"single_core_time={singlecore.total_time}")
    lines.append(f"multicore_time={multicore.total_time}")
    lines.append(f"time_saved={singlecore.total_time - multicore.total_time}")
    lines.append(f"speedup={singlecore.total_time / multicore.total_time:.2f}x")
    lines.append(f"throughput={multicore.throughput:.2f}")

    total_busy = sum(multicore.core_busy)
    total_capacity = multicore.total_time * cores
    overall_utilization = (total_busy / total_capacity) * 100 if total_capacity else 0.0
    lines.append(f"overall_utilization={overall_utilization:.2f}%")

    for core_index, utilization in enumerate(multicore.core_utilization):
        lines.append(f"core_{core_index}_utilization={utilization:.2f}%")

    write_lines(filename, lines)


def main():
    tasks_file = "input.txt"

    cores, tasks = load_tasks_from_file(tasks_file)

    multicore = simulate(tasks, cores)
    singlecore = simulate(tasks, 1)

    trace_lines = build_trace_lines(multicore)

    write_lines("trace.log", trace_lines)
    write_task_log(multicore.tasks, "tasks_final.log")
    write_core_log(multicore, "cores_final.log")
    write_sim_stats("sim_stats.log", multicore, singlecore, cores)

    print("HALT")
    print("tasks completed =", len(multicore.tasks))
    print("execution time =", multicore.total_time)
    print("wrote trace.log, tasks_final.log, cores_final.log, sim_stats.log")


if __name__ == "__main__":
    main()
