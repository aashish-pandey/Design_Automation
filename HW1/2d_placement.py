# #netlist data format
# # data = {
# #     'grid_size': ,
# #     'cells': {

# #     },
# #     'nets': {

# #     }
# # }



# # Algorithm from class note
#         # Procedure SimulatedAnnealing
#         # curSolution = random initial solution
#         # T = T0 // initial temperature eg. T0 = 40,000
#         # while (T > T freez) do // eg. Tfreez = 0.1)
#         # for i=1 to NUM_MOVES_PER_TEMP_STEP do
#         # nextSol = perturb (curSolution)
#         # ∆cost = cost(nextSol) – cost(curSolution)
#         # if acceptMove (∆cost, T) then
#         # curSolution = nextSol // accept the move
#         # end for
#         # T = coolDown (T ) // eg. T = 0.95 * T
#         # end while

#         # Procedure acceptMove (∆cost, T)
#         # if ∆cost ≤ 0 then return TRUE // always accept a good move
#         # else
#         # boltz = e-∆cost / k.T // Boltzmann probability function
#         # r = random(0,1) // uniform rand # between 0&1
#         # if r < boltz then return TRUE
#         # else return FALSE
# import copy
# import math
# import random
# import Ptest_1000 as placement_data
# import os
# import csv
# import matplotlib.pyplot as plt
# import shutil
# import pprint
# import time
# import tracemalloc

# def write_params(seed, T0, Tfreez, moves, k, cool_down, optimal_cost, runtime, memory_usage):

#     os.makedirs("logs", exist_ok=True)

#     with open("logs/params.txt", "w") as f:
#         f.write(f"Random seed = {seed}\n")
#         f.write(f"T0 = {T0}\n")
#         f.write(f"Tfreez = {Tfreez}\n")
#         f.write(f"NUM_MOVES_PER_TEMP_STEP = {moves}\n")
#         f.write(f"k = {k}\n")
#         f.write(f"cool_down_factor = {cool_down}\n\n")
#         f.write(f"optimal_cost = {optimal_cost}\n")
#         f.write(f"runtime = {runtime:.2f} seconds\n")
#         f.write(f"peak_memory_usage = {memory_usage / (1024 * 1024):.2f} MB\n")
#     print("✅ logs/params.txt written")

# def write_output(original, output):

#     os.makedirs("logs", exist_ok=True)

#     with open("logs/output.py", "w") as f:
#         f.write("original_data = ")
#         f.write(pprint.pformat(original))
#         f.write("\n\noutput_data = ")
#         f.write(pprint.pformat(output))

#     print("✅ logs/output.py written")

# def reset_logs():
#     if os.path.exists("logs"):
#         shutil.rmtree("logs")
#         print("Old logs folder removed.")
#     else:
#         print("No logs folder found.")
# def plot_sa_logs():
#     cost_path = "logs/cost_log.csv"
#     move_path = "logs/move_log.csv"

#     if not os.path.exists(cost_path) or not os.path.exists(move_path):
#         print("Log files not found.")
#         return

#     # -------- Read cost log --------
#     current_cost = []
#     best_cost = []

#     with open(cost_path, newline="") as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             current_cost.append(float(row["current_cost"]))
#             best_cost.append(float(row["best_cost"]))

#     # -------- Read move log --------
#     acceptance = []

#     with open(move_path, newline="") as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             acceptance.append(float(row["acceptance_ratio"]))

#     # -------- Plot 1: Current cost --------
#     plt.figure()
#     plt.plot(current_cost)
#     plt.xlabel("Temperature Step")
#     plt.ylabel("Current Cost")
#     plt.title("SA Current Cost Evolution")
#     plt.grid(True)
#     plt.savefig("logs/current_cost.png")
#     plt.close()

#     # -------- Plot 2: Best cost --------
#     plt.figure()
#     plt.plot(best_cost)
#     plt.xlabel("Temperature Step")
#     plt.ylabel("Best Cost")
#     plt.title("SA Best Cost Evolution")
#     plt.grid(True)
#     plt.savefig("logs/best_cost.png")
#     plt.close()

#     # -------- Plot 3: Acceptance ratio --------
#     plt.figure()
#     plt.plot(acceptance)
#     plt.xlabel("Temperature Step")
#     plt.ylabel("Acceptance Ratio")
#     plt.title("SA Acceptance Evolution")
#     plt.grid(True)
#     plt.savefig("logs/acceptance_curve.png")
#     plt.close()

#     print("Plots saved in logs/ folder.")



# def log_sa(kind, a, b, c):
#     """
#     kind = "cost" or "move"

#     COST:
#         a → temperature
#         b → current cost
#         c → best cost

#     MOVE:
#         a → attempted moves
#         b → accepted moves
#         c → acceptance ratio
#     """

#     os.makedirs("logs", exist_ok=True)

#     if kind == "cost":
#         path = "logs/cost_log.csv"
#         if not os.path.exists(path):
#             with open(path, "w") as f:
#                 f.write("temperature,current_cost,best_cost\n")

#         with open(path, "a") as f:
#             f.write(f"{a},{b},{c}\n")

#     elif kind == "move":
#         path = "logs/move_log.csv"
#         if not os.path.exists(path):
#             with open(path, "w") as f:
#                 f.write("attempted,accepted,acceptance_ratio\n")

#         with open(path, "a") as f:
#             f.write(f"{a},{b},{c}\n")



# def acceptMove(delta_cost, T):
#     if(delta_cost <= 0):
#         return True 
#     else:
#         boltz = math.exp(-delta_cost / (k * T))
#         r = random.random()
#         if r < boltz:
#             return True
#         else:
#             return False

# def coolDown(T):
#     return cool_down_factor * T 

# def random_initial_solution(data):
#     #data provided can be considered as a random initial solution
#     pass

# def perturb(curSolution, positions):
#     # randomly select a movable cell and move it to a random position from the available positions

#     cells = curSolution['cells']
#     movable_cells = [cell for cell in cells if cells[cell]['fixed'] == False]
#     selected_cell = random.choice(movable_cells)
#     new_position = random.choice(positions)
#     candidate_solution = copy.deepcopy(curSolution)
#     # update the position of the selected cell
#     candidate_solution['cells'][selected_cell]['position'] = new_position
    
#     return candidate_solution, selected_cell

# #the question does not consider the manhattan distance as the cost function
# # def cost(solution):
# #     nets = solution['nets']
# #     cst = 0
# #     for net in nets:
# #         cell1, cell2 = net['cells']
# #         pos1 = solution['cells'][cell1]['position']
# #         pos2 = solution['cells'][cell2]['position']
        
# #         cst += abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
# #     return cst

# def cost(solution):

#     total_hpwl = 0

#     for net in solution["nets"]:

#         xs = []
#         ys = []

#         for cell in net["cells"]:
#             x, y = solution["cells"][cell]["position"]
#             xs.append(x)
#             ys.append(y)

#         hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
#         total_hpwl += hpwl

#     return total_hpwl


# def stimulated_anneanling(data, positions):

#     # curSolution = random_initial_solution(data)
#     curSolution = data
#     bestSolution = copy.deepcopy(curSolution)
#     T = T0 

#     while T > Tfreez:
#         attempted_moves = 0
#         accepted_moves = 0
#         initial_cost = cost(curSolution)
#         for i in range(NUM_MOVES_PER_TEMP_STEP):
#             nextSolution, changed_Cell = perturb(curSolution, positions)
#             attempted_moves += 1
#             delta_cost = cost(nextSolution) - cost(curSolution)
#             if acceptMove(delta_cost, T):
#                 #change the positions 
#                 positions.remove(nextSolution['cells'][changed_Cell]['position'])
#                 positions.append(curSolution['cells'][changed_Cell]['position'])
#                 curSolution = nextSolution
#                 accepted_moves += 1
#                 if cost(curSolution) < cost(bestSolution):
#                     bestSolution = copy.deepcopy(curSolution)
#         T = coolDown(T)
#         best_cost = cost(bestSolution)
#         # print(f"Temperature: {T:.2f}, Initial Cost: {initial_cost}, Best Cost: {best_cost}")
#         log_sa("cost", T, initial_cost, best_cost)
#         if(attempted_moves == 0):
#             acceptance_rate = 0
#         else:        
#             acceptance_rate = accepted_moves / attempted_moves
#         # print(f"Attempted moves: {attempted_moves}, Accepted moves: {accepted_moves}, Acceptance rate: {acceptance_rate}")
#         log_sa("move", attempted_moves, accepted_moves, acceptance_rate)
#     return bestSolution

# ## data preperation for stimulated annealing algorithm

# def get_movable_position(data):
#     grid_size = data['grid_size']
#     cells = []
#     for i in range(grid_size):
#         for j in range(grid_size):
#             cells.append((i, j))

#     cell_pos = data['cells']
#     for cell in cell_pos:
#         pos = cell_pos[cell]['position']
#         if pos in cells:
#             cells.remove(pos)
#     return cells




# data = placement_data.data
# positions = get_movable_position(data)
# # print(positions)
# cost_value = cost(data)
# print("Cost of the initial position:", cost_value)
# reset_logs()


# #seed
# random.seed(42)
# ## Stimulated Annealing for 2D placement problem
# #initial Variables
# T0 = 100
# Tfreez = 0.1
# NUM_MOVES_PER_TEMP_STEP = 4000
# k = 1
# cool_down_factor = 0.995

# tracemalloc.start()
# start = time.time()
# optimal_position = stimulated_anneanling(data, positions)
# end = time.time()
# current, peak = tracemalloc.get_traced_memory()
# tracemalloc.stop()
# runtime = end - start
# write_output(data, optimal_position)

# cost_value = cost(optimal_position)
# write_params(seed=42, T0=T0, Tfreez=Tfreez, moves=NUM_MOVES_PER_TEMP_STEP, k=k, cool_down=cool_down_factor, optimal_cost=cost_value, runtime=runtime, memory_usage=peak)
# print(f"T0: {T0}, Tfreez: {Tfreez}, NUM_MOVES_PER_TEMP_STEP: {NUM_MOVES_PER_TEMP_STEP}, k: {k}, Cost: {cost_value}")
# plot_sa_logs()


import copy
import math
import random
import Ptest_25 as placement_data
import os
import csv
import matplotlib.pyplot as plt
import shutil
import pprint
import time
import tracemalloc


# ==============================
# GLOBAL TIME LIMIT (1 hour)
# ==============================

TIME_LIMIT = 3600   # seconds


# ==============================
# Logging Utilities
# ==============================

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

    print("✅ logs/params.txt written")


def write_output(original, output):

    os.makedirs("logs", exist_ok=True)

    with open("logs/output.py", "w") as f:
        f.write("original_data = ")
        f.write(pprint.pformat(original))
        f.write("\n\noutput_data = ")
        f.write(pprint.pformat(output))

    print("✅ logs/output.py written")


def reset_logs():
    if os.path.exists("logs"):
        shutil.rmtree("logs")
        print("Old logs folder removed.")


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
        print("Log files not found.")
        return

    current_cost, best_cost = [], []

    with open(cost_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            current_cost.append(float(row["current_cost"]))
            best_cost.append(float(row["best_cost"]))

    acceptance = []

    with open(move_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            acceptance.append(float(row["acceptance_ratio"]))

    plt.figure()
    plt.plot(current_cost)
    plt.title("Current Cost")
    plt.grid(True)
    plt.savefig("logs/current_cost.png")
    plt.close()

    plt.figure()
    plt.plot(best_cost)
    plt.title("Best Cost")
    plt.grid(True)
    plt.savefig("logs/best_cost.png")
    plt.close()

    plt.figure()
    plt.plot(acceptance)
    plt.title("Acceptance Ratio")
    plt.grid(True)
    plt.savefig("logs/acceptance_curve.png")
    plt.close()

    print("Plots saved.")


# ==============================
# SA Core Functions
# ==============================

def acceptMove(delta_cost, T):
    if delta_cost <= 0:
        return True

    boltz = math.exp(-delta_cost / (k * T))
    return random.random() < boltz


def coolDown(T):
    return cool_down_factor * T


def perturb(curSolution, positions):

    cells = curSolution['cells']
    movable = [c for c in cells if not cells[c]['fixed']]

    selected = random.choice(movable)
    new_pos = random.choice(positions)

    candidate = copy.deepcopy(curSolution)
    candidate['cells'][selected]['position'] = new_pos

    return candidate, selected


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


# ==============================
# Simulated Annealing with Time Limit
# ==============================

def stimulated_anneanling(data, positions, start_time):

    curSolution = data
    bestSolution = copy.deepcopy(curSolution)
    T = T0

    while T > Tfreez:

        if time.time() - start_time >= TIME_LIMIT:
            print("\n⏰ Time limit reached — stopping SA.")
            return bestSolution

        attempted = 0
        accepted = 0
        initial_cost = cost(curSolution)

        for _ in range(NUM_MOVES_PER_TEMP_STEP):

            if time.time() - start_time >= TIME_LIMIT:
                print("\n⏰ Time limit reached during moves.")
                return bestSolution

            nextSol, changed = perturb(curSolution, positions)
            attempted += 1

            delta = cost(nextSol) - cost(curSolution)

            if acceptMove(delta, T):

                positions.remove(nextSol['cells'][changed]['position'])
                positions.append(curSolution['cells'][changed]['position'])

                curSolution = nextSol
                accepted += 1

                if cost(curSolution) < cost(bestSolution):
                    bestSolution = copy.deepcopy(curSolution)

        T = coolDown(T)

        best_cost = cost(bestSolution)

        log_sa("cost", T, initial_cost, best_cost)

        ratio = accepted / attempted if attempted else 0
        log_sa("move", attempted, accepted, ratio)

    return bestSolution


# ==============================
# Helper
# ==============================

def get_movable_position(data):

    grid = data['grid_size']
    cells = [(i, j) for i in range(grid) for j in range(grid)]

    for c in data['cells'].values():
        if c['position'] in cells:
            cells.remove(c['position'])

    return cells


# ==============================
# Main Execution
# ==============================

reset_logs()

random.seed(42)

data = placement_data.data
positions = get_movable_position(data)

print("Initial cost:", cost(data))

T0 = 1
Tfreez = 0.1
NUM_MOVES_PER_TEMP_STEP = 40
k = 1
cool_down_factor = 0.995

tracemalloc.start()
start = time.time()

optimal = stimulated_anneanling(data, positions, start)

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

print("\n🔥 SA Finished")
print("Final cost:", final_cost)
print(f"Runtime: {runtime:.2f}s")
