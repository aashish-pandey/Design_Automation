import copy
import math
import random
# import ptest1000_aas as placement_data
import Ptest_10000 as placement_data
import os
import csv
import matplotlib.pyplot as plt
import shutil
import pprint
import time
import tracemalloc


# =================================
# CONFIG
# =================================

RUN_MODE = "probe"   # "probe" or "full"
TIME_LIMIT = 3600    # full run limit (seconds)
PROBE_TIME = 300      # seconds


# =================================
# Logging Utilities
# =================================

def write_params(seed, T0, Tfreez, moves, k, cool_down, optimal_cost, runtime, memory_usage):
    os.makedirs("logs", exist_ok=True)
    with open("logs/params.txt", "w") as f:
        f.write(f"Random seed = {seed}\n")
        f.write(f"T0 = {T0}\n")
        f.write(f"Tfreez = {Tfreez}\n")
        f.write(f"NUM_MOVES_PER_TEMP_STEP = {moves}\n")
        f.write(f"k = {k}\n")
        f.write(f"cool_down_factor = {cool_down}\n\n")
        f.write(f"optimal_cost = {optimal_cost}\n")
        f.write(f"runtime = {runtime:.2f} seconds\n")
        f.write(f"peak_memory_usage = {memory_usage / (1024 * 1024):.2f} MB\n")
    print("✅ params.txt written")


def write_output(original, output):
    os.makedirs("logs", exist_ok=True)
    with open("logs/output.py", "w") as f:
        f.write("original_data = ")
        f.write(pprint.pformat(original))
        f.write("\n\noutput_data = ")
        f.write(pprint.pformat(output))
    print("✅ output.py written")


def reset_logs():
    if os.path.exists("logs"):
        shutil.rmtree("logs")
        print("Old logs removed.")


def log_sa(kind, a, b, c):
    os.makedirs("logs", exist_ok=True)

    if kind == "cost":
        path = "logs/cost_log.csv"
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("temperature,current_cost,best_cost\n")
        with open(path, "a") as f:
            f.write(f"{a},{b},{c}\n")

    elif kind == "move":
        path = "logs/move_log.csv"
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("attempted,accepted,acceptance_ratio\n")
        with open(path, "a") as f:
            f.write(f"{a},{b},{c}\n")


def plot_sa_logs():
    cost_path = "logs/cost_log.csv"
    move_path = "logs/move_log.csv"

    if not os.path.exists(cost_path) or not os.path.exists(move_path):
        print("No logs found.")
        return

    cur, best, acc = [], [], []

    with open(cost_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.append(float(row["current_cost"]))
            best.append(float(row["best_cost"]))

    with open(move_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            acc.append(float(row["acceptance_ratio"]))

    plt.figure()
    plt.plot(cur)
    plt.title("Current Cost")
    plt.grid(True)
    plt.savefig("logs/current_cost.png")
    plt.close()

    plt.figure()
    plt.plot(best)
    plt.title("Best Cost")
    plt.grid(True)
    plt.savefig("logs/best_cost.png")
    plt.close()

    plt.figure()
    plt.plot(acc)
    plt.title("Acceptance Ratio")
    plt.grid(True)
    plt.savefig("logs/acceptance.png")
    plt.close()

    print("Plots saved.")


# =================================
# SA Core
# =================================

def acceptMove(delta_cost, T):
    if delta_cost <= 0:
        return True
    return random.random() < math.exp(-delta_cost / (k * T))


def coolDown(T):
    return cool_down_factor * T


def perturb(sol, positions, swap_prob=0.4):
    """
    Mixed perturbation operator:
    - relocation move (default)
    - swap move (with probability swap_prob)

    Returns:
        candidate_solution
        move_info dict describing move type
    """

    candidate = copy.deepcopy(sol)

    movable = [c for c in sol['cells'] if not sol['cells'][c]['fixed']]

    # ---------- SWAP MOVE ----------
    if len(movable) >= 2 and random.random() < swap_prob:

        c1, c2 = random.sample(movable, 2)

        p1 = sol['cells'][c1]['position']
        p2 = sol['cells'][c2]['position']

        candidate['cells'][c1]['position'] = p2
        candidate['cells'][c2]['position'] = p1

        return candidate, {
            "type": "swap",
            "cells": (c1, c2),
            "old_positions": (p1, p2)
        }

    # ---------- RELOCATION MOVE ----------
    else:

        c = random.choice(movable)

        old_pos = sol['cells'][c]['position']
        new_pos = random.choice(positions)

        candidate['cells'][c]['position'] = new_pos

        return candidate, {
            "type": "move",
            "cell": c,
            "old_pos": old_pos,
            "new_pos": new_pos
        }


def cost(solution):
    total = 0
    for net in solution["nets"]:
        xs, ys = [], []
        for cell in net["cells"]:
            x, y = solution["cells"][cell]["position"]
            xs.append(x)
            ys.append(y)
        total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return total


def flush_step_logs(T, init_cost, best_solution, attempted, accepted):
    """Always write one log point for the current temperature step."""
    best_cost = cost(best_solution)
    log_sa("cost", T, init_cost, best_cost)
    ratio = (accepted / attempted) if attempted else 0
    log_sa("move", attempted, accepted, ratio)


def simulated_annealing(data, positions, start_time, time_limit):
    cur = data
    best = copy.deepcopy(cur)
    T = T0

    while T > Tfreez:

        attempted = 0
        accepted = 0
        init_cost = cost(cur)

        # If we are already out of time BEFORE doing this temp step,
        # still flush a log point so plots exist.
        if time.time() - start_time >= time_limit:
            print("⏰ Time limit reached (before temp step). Logging and stopping.")
            flush_step_logs(T, init_cost, best, attempted, accepted)
            return best

        for _ in range(NUM_MOVES_PER_TEMP_STEP):

            # If time limit hits mid-step, flush logs with partial stats.
            if time.time() - start_time >= time_limit:
                print("⏰ Time limit reached (during moves). Logging and stopping.")
                flush_step_logs(T, init_cost, best, attempted, accepted)
                return best

            nextSol, move = perturb(cur, positions)
            attempted += 1

            delta = cost(nextSol) - cost(cur)

            if acceptMove(delta, T):

                if move["type"] == "move":
                    positions.remove(move["new_pos"])
                    positions.append(move["old_pos"])

                # swap move → positions unchanged

                cur = nextSol
                accepted += 1

                if cost(cur) < cost(best):
                    best = copy.deepcopy(cur)

        # normal end of temp step
        T = coolDown(T)
        flush_step_logs(T, init_cost, best, attempted, accepted)

    return best


# =================================
# Helpers
# =================================

def estimate_T0(solution, positions, samples=200):
    deltas = []
    for _ in range(samples):
        nxt, _ = perturb(solution, positions)
        d = cost(nxt) - cost(solution)
        if d > 0:
            deltas.append(d)

    if not deltas:
        return 1

    avg = sum(deltas) / len(deltas)
    return -avg / math.log(0.9)


def get_positions(data):
    grid = data['grid_size']
    cells = [(i, j) for i in range(grid) for j in range(grid)]
    for c in data['cells'].values():
        if c['position'] in cells:
            cells.remove(c['position'])
    return cells


def diagnostic_run(data, positions):
    global T0
    print("🔬 Estimating T0...")
    # T0 = estimate_T0(data, positions)
    T0 = 0.000125
    print("Estimated T0:", T0)

    print("🚀 Diagnostic SA running...")
    start = time.time()
    return simulated_annealing(data, positions, start, PROBE_TIME)


# =================================
# Main
# =================================

reset_logs()
random.seed(50)

data = placement_data.data
positions = get_positions(data)

print("Initial cost:", cost(data))

# baseline params (you can tune these)
T0 = 10
Tfreez = 0.0001
NUM_MOVES_PER_TEMP_STEP = 10000
k = 1
cool_down_factor = 0.90
tracemalloc.start()
start = time.time()

if RUN_MODE == "probe":
    optimal = diagnostic_run(data, positions)
else:
    print("🔥 Full SA running...")
    optimal = simulated_annealing(data, positions, start, TIME_LIMIT)

end = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

runtime = end - start

write_output(data, optimal)

final_cost = cost(optimal)

write_params(
    seed=42,
    T0=T0,
    Tfreez=Tfreez,
    moves=NUM_MOVES_PER_TEMP_STEP,
    k=k,
    cool_down=cool_down_factor,
    optimal_cost=final_cost,
    runtime=runtime,
    memory_usage=peak
)

plot_sa_logs()

print("\n🔥 SA finished")
print("Final cost:", final_cost)
print("Runtime:", runtime)
