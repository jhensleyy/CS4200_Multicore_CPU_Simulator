# Simple Multicore CPU Simulator

## Overview

This project is a simplified multicore CPU simulator written in Python. It models how multiple CPU cores execute tasks that arrive over time 
and compares multicore performance against single-core performance.

The simulator focuses on:

- two or more CPU cores executing tasks
- task distribution across available cores
- execution time comparison between multicore and single-core execution
- throughput and core utilization

This project helps demonstrate key operating systems and computer architecture concepts such as multicore processing, parallel execution, 
and workload distribution.

## Concepts Explored

- multicore architectures
- parallel execution
- workload distribution
- execution time improvement
- throughput
- core utilization

## Files

- `MultiCoreCPU_Project.py`  
  Main simulator program

- `input.txt`  
  Input file containing the number of cores and the list of tasks

- `trace.log`  
  Timeline of task start and end events

- `tasks_final.log`  
  Final task results including assigned core, wait time, and turnaround time

- `cores_final.log`  
  Per-core schedule, busy time, and utilization

- `sim_stats.log`  
  Summary statistics including execution time, speedup, throughput, and utilization

## Input Format

The simulator reads from a fixed input file named `input.txt`.

### Format

text
<number_of_cores>
<number_of_tasks>
<task_id> <arrival_time> <duration>
<task_id> <arrival_time> <duration>
