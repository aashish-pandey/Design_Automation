"""
===============================================================
Simulated Annealing Placement Optimizer
===============================================================

Authors:
    Bhatta, Pandey

Course:
    Design Automation

Description:
    This program performs VLSI placement optimization using
    Simulated Annealing (SA) to minimize Half-Perimeter Wire Length (HPWL).

    The algorithm swaps movable cells and uses the Metropolis
    acceptance criterion to explore the solution space.

---------------------------------------------------------------
EXECUTION INSTRUCTIONS
---------------------------------------------------------------

1. Place benchmark file in the same directory:
       Place_5000.py
   (must contain: data = {cells:..., nets:...})

2. Run the program:

       python3 Pandey_Bhatta_SA.py

3. Output will be generated in:

       output_<benchmark_name>/

   including:
       • optimized placement (Python file)
       • annealing log (CSV)
       • convergence plots

---------------------------------------------------------------
DEPENDENCIES
---------------------------------------------------------------
Python 3.x
numpy
matplotlib

Install if needed:
    pip install numpy matplotlib
===============================================================
"""
import math
import random
import time
import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import Ptest_500 as placement_data


def save_python_netlist(output_dir, data, filename="Bhatta_Pandey_Ptest500.py"):
    """
    Save optimized data as an importable Python file.
    """

    path = os.path.join(output_dir, filename)

    with open(path, "w") as f:
        f.write("# Auto-generated optimized placement\n")
        f.write("data = ")
        f.write(repr(data))   # preserves Python structure

    print("Optimized netlist saved as Python file ✔")



# -------------------------------------------------
# HPWL CALCULATION
# -------------------------------------------------
def calculate_net_hpwl(net_cells, cells):
    p1 = cells[net_cells[0]]['position']
    p2 = cells[net_cells[1]]['position']
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


# -------------------------------------------------
# PLOT GENERATION
# -------------------------------------------------
def generate_plots(output_dir, log_data):

    steps = log_data[:, 0]
    temp = log_data[:, 1]
    best = log_data[:, 2]
    accepted = log_data[:, 4]
    prob = log_data[:, 5]

    # -------------------------
    # Temperature Curve
    # -------------------------
    plt.figure()
    plt.plot(steps, temp)
    plt.xlabel("Annealing Step")
    plt.ylabel("Temperature")
    plt.title("Temperature Decay")
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "temperature_curve.png"), dpi=200)
    plt.close()

    # -------------------------
    # Boltzmann Curve
    # -------------------------
    plt.figure()
    plt.plot(steps, prob)
    plt.xlabel("Annealing Step")
    plt.ylabel("Boltzmann Probability")
    plt.title("Boltzmann Acceptance Probability")
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "boltzmann_curve.png"), dpi=200)
    plt.close()

    # -------------------------
    # Accepted Moves Curve
    # -------------------------
    plt.figure()
    plt.plot(steps, accepted)
    plt.xlabel("Annealing Step")
    plt.ylabel("Accepted Moves")
    plt.title("Accepted Moves per Temperature")
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "accepted_moves_curve.png"), dpi=200)
    plt.close()

    # -------------------------
    # Cost Curve
    # -------------------------
    plt.figure()
    plt.plot(steps, best)
    plt.xlabel("Annealing Step")
    plt.ylabel("Best HPWL")
    plt.title("Cost Convergence")
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "cost_curve.png"), dpi=200)
    plt.close()


# -------------------------------------------------
# SIMULATED ANNEALING
# -------------------------------------------------
def solve_sa(data, seed=68, output_tag="Bhatta_Pandey_Ptest500"):

    random.seed(seed)

    cells = data['cells']
    nets = data['nets']

    movable_ids = [cid for cid, info in cells.items() if not info['fixed']]

    cell_to_nets = {cid: [] for cid in cells}
    for i, net in enumerate(nets):
        for cid in net['cells']:
            cell_to_nets[cid].append(i)

    current_hpwl = sum(
        calculate_net_hpwl(net['cells'], cells)
        for net in nets
    )

    best_hpwl = current_hpwl

    best_placement = {
        cid: tuple(cells[cid]['position'])
        for cid in movable_ids
    }

    num_movable = len(movable_ids)
    data_len = len(nets)

    T = 10 
    alpha = 0.999 

    frozen_temp = 1e-19

    max_stagnant_steps = 1500 if data_len < 1000 else 2000
    stagnant_counter = 0
    prev_best = best_hpwl

    start_time = time.time()

    print(f"\nStarting SA — Initial HPWL: {current_hpwl}")

    # fast log buffers
    log_step, log_temp, log_best, log_current = [], [], [], []
    log_accept, log_prob, log_time = [], [], []

    step = 0

    while T > frozen_temp:

        elapsed = time.time() - start_time
        if elapsed > 3600:
            print("Stopping early (time guard)")
            break

        moves_per_temp = int(max(data_len, T * data_len))
        accepted_moves = 0

        for _ in range(moves_per_temp):

            c1 = random.choice(movable_ids)
            c2 = random.choice(movable_ids)
            if c1 == c2:
                continue

            pos1 = cells[c1]['position']
            pos2 = cells[c2]['position']

            affected = set(cell_to_nets[c1] + cell_to_nets[c2])

            hpwl_before = sum(
                calculate_net_hpwl(nets[i]['cells'], cells)
                for i in affected
            )

            cells[c1]['position'], cells[c2]['position'] = pos2, pos1

            hpwl_after = sum(
                calculate_net_hpwl(nets[i]['cells'], cells)
                for i in affected
            )

            delta = hpwl_after - hpwl_before

            accept = False
            if delta < 0:
                accept = True
            else:
                if random.random() < math.exp(min(0, -delta / T)):
                    accept = True

            if accept:
                accepted_moves += 1
                current_hpwl += delta
                if current_hpwl < best_hpwl:
                    best_hpwl = current_hpwl
                    best_placement = {
                        cid: tuple(cells[cid]['position'])
                        for cid in movable_ids
                    }
            else:
                cells[c1]['position'], cells[c2]['position'] = pos1, pos2

        if best_hpwl < prev_best:
            stagnant_counter = 0
        else:
            stagnant_counter += 1
        prev_best = best_hpwl

        step += 1
        log_step.append(step)
        log_temp.append(T)
        log_best.append(best_hpwl)
        log_current.append(current_hpwl)
        log_accept.append(accepted_moves)
        log_prob.append(math.exp(-1 / T))
        log_time.append(elapsed)

        print(f"Temp: {T:.9f} | HPWL: {current_hpwl} | Best: {best_hpwl} | "
              f"Stagnant: {stagnant_counter}/{max_stagnant_steps} | "
              f"Time: {elapsed:.1f}s")

        if stagnant_counter >= max_stagnant_steps:
            print("Stopping early (no improvement)")
            break

        T *= alpha

    for cid, pos in best_placement.items():
        cells[cid]['position'] = pos

    # save output
    output_dir = f"output_{output_tag}"
    os.makedirs(output_dir, exist_ok=True)

    log_data = np.column_stack((
        log_step,
        log_temp,
        log_best,
        log_current,
        log_accept,
        log_prob,
        log_time
    ))

    csv_path = os.path.join(output_dir, "annealing_log.csv")

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "step","temperature","best_hpwl","current_hpwl",
            "accepted_moves","boltzmann_prob","elapsed_time_sec"
        ])
        writer.writerows(log_data)

    generate_plots(output_dir, log_data)
    save_python_netlist(output_dir, data)

    print(f"\nOutput saved in: {output_dir}")
    print("Plots generated ✔")

    return data


# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":

    data = placement_data.data

    result = solve_sa(data, output_tag="Bhatta_Pandey_Ptest500")

    final_hpwl = sum(
        calculate_net_hpwl(net['cells'], result['cells'])
        for net in result['nets']
    )

    print("\nSearch Complete")
    print("Final HPWL:", final_hpwl)
