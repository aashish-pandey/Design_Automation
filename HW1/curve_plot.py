import csv
import os
import matplotlib.pyplot as plt

def plot_sa_logs():
    cost_path = "logs/cost_log.csv"
    move_path = "logs/move_log.csv"

    if not os.path.exists(cost_path) or not os.path.exists(move_path):
        print("Log files not found.")
        return

    # -------- Read cost log --------
    current_cost = []
    best_cost = []

    with open(cost_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            current_cost.append(float(row["current_cost"]))
            best_cost.append(float(row["best_cost"]))

    # -------- Read move log --------
    acceptance = []

    with open(move_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            acceptance.append(float(row["acceptance_ratio"]))

    # -------- Plot 1: Current cost --------
    plt.figure()
    plt.plot(current_cost)
    plt.xlabel("Temperature Step")
    plt.ylabel("Current Cost")
    plt.title("SA Current Cost Evolution")
    plt.grid(True)
    plt.savefig("logs/current_cost.png")
    plt.close()

    # -------- Plot 2: Best cost --------
    plt.figure()
    plt.plot(best_cost)
    plt.xlabel("Temperature Step")
    plt.ylabel("Best Cost")
    plt.title("SA Best Cost Evolution")
    plt.grid(True)
    plt.savefig("logs/best_cost.png")
    plt.close()

    # -------- Plot 3: Acceptance ratio --------
    plt.figure()
    plt.plot(acceptance)
    plt.xlabel("Temperature Step")
    plt.ylabel("Acceptance Ratio")
    plt.title("SA Acceptance Evolution")
    plt.grid(True)
    plt.savefig("logs/acceptance_curve.png")
    plt.close()

    print("Plots saved in logs/ folder.")

plot_sa_logs()