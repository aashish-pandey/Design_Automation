import os
from heapq import heappush, heappop
from collections import defaultdict

# ==============================
# IMPORT NETLIST (same style as yours)
# ==============================
import Rtest_500_5000 as netlist   # <-- change here when needed

data = netlist.data
grid_size = data["grid_size"]
nets_data = data["nets"]

# ==============================
# CONFIGURATION
# ==============================
LMIN = 2
LMAX = 9

WIRE_COST = 1
VIA_COST = 2

CAPACITY = 1

MAX_ITERS = 30

ALPHA_PRESENT = 4.0     # penalty for current overflow
BETA_HISTORY = 1.0      # penalty for past overflow
HISTORY_INCREMENT = 1.0

MARGIN = 8

LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

# ==============================
# LAYER RULES
# ==============================
def is_vertical(layer):
    return layer % 2 == 0


# ==============================
# NEIGHBOR GENERATION
# ==============================
def neighbors(x, y, layer, bbox):
    xmin, xmax, ymin, ymax = bbox

    if is_vertical(layer):
        for ny in (y - 1, y + 1):
            if xmin <= x <= xmax and ymin <= ny <= ymax:
                yield (x, ny, layer), WIRE_COST
    else:
        for nx in (x - 1, x + 1):
            if xmin <= nx <= xmax and ymin <= y <= ymax:
                yield (nx, y, layer), WIRE_COST

    if layer > LMIN:
        yield (x, y, layer - 1), VIA_COST
    if layer < LMAX:
        yield (x, y, layer + 1), VIA_COST


# ==============================
# HEURISTIC
# ==============================
def heuristic(x, y, L, goal_xy):
    gx, gy = goal_xy
    manhattan = abs(x - gx) + abs(y - gy)
    via_back = VIA_COST * abs(L - LMIN)
    return manhattan + via_back


# ==============================
# CONGESTION COST MODEL
# ==============================
def congestion_cost(base_cost, v, usage, history):
    predicted_usage = usage[v] + 1
    overflow = max(0, predicted_usage - CAPACITY)

    return (
        base_cost
        + ALPHA_PRESENT * overflow
        + BETA_HISTORY * history[v]
    )


# ==============================
# A* WITH NEGOTIATED CONGESTION
# ==============================
def astar_route(src, dst, usage, history):

    x1, y1 = src
    x2, y2 = dst

    xmin = max(0, min(x1, x2) - MARGIN)
    xmax = min(grid_size - 1, max(x1, x2) + MARGIN)
    ymin = max(0, min(y1, y2) - MARGIN)
    ymax = min(grid_size - 1, max(y1, y2) + MARGIN)

    bbox = (xmin, xmax, ymin, ymax)

    start = (x1, y1, LMIN)
    goal_xy = (x2, y2)

    pq = []
    heappush(pq, (heuristic(x1, y1, LMIN, goal_xy), 0, start))

    g_cost = {start: 0}
    parent = {}

    while pq:
        f, cost, u = heappop(pq)

        if cost != g_cost.get(u, None):
            continue

        x, y, L = u

        if (x, y) == goal_xy and L == LMIN:
            path = [u]
            while u in parent:
                u = parent[u]
                path.append(u)
            path.reverse()
            return path

        for v, base_w in neighbors(x, y, L, bbox):

            nx, ny, nL = v
            if not (0 <= nx < grid_size and 0 <= ny < grid_size):
                continue

            step = congestion_cost(base_w, v, usage, history)
            new_cost = cost + step

            if new_cost < g_cost.get(v, float("inf")):
                g_cost[v] = new_cost
                parent[v] = u
                f_new = new_cost + heuristic(nx, ny, nL, goal_xy)
                heappush(pq, (f_new, new_cost, v))

    return None


# ==============================
# MAIN NEGOTIATED CONGESTION ENGINE
# ==============================
def main():

    nets = []
    for name, info in nets_data.items():
        (x1, y1), (x2, y2) = info["pins"]
        manh = abs(x1 - x2) + abs(y1 - y2)
        nets.append((name, (x1, y1), (x2, y2), manh))

    # Route shorter nets first (helps convergence)
    nets.sort(key=lambda x: x[3])

    history = defaultdict(float)
    final_routes = {}

    for iteration in range(1, MAX_ITERS + 1):

        print(f"\n=== Iteration {iteration} ===")

        usage = defaultdict(int)
        routes = {}
        failed = 0

        # Route all nets
        for name, src, dst, _ in nets:

            path = astar_route(src, dst, usage, history)

            if path is None:
                failed += 1
                routes[name] = None
                continue

            routes[name] = path

            for node in path:
                usage[node] += 1

        # Check congestion
        overflow_resources = []
        total_overflow = 0

        for node, u in usage.items():
            if u > CAPACITY:
                overflow = u - CAPACITY
                total_overflow += overflow
                overflow_resources.append(node)

        print("Failed nets:", failed)
        print("Total overflow:", total_overflow)

        # If no congestion and no failure → done
        if failed == 0 and total_overflow == 0:
            print("Routing converged successfully.")
            final_routes = routes
            break

        # Update history penalty
        for node in overflow_resources:
            history[node] += HISTORY_INCREMENT

        final_routes = routes

    # ==============================
    # Compute final cost
    # ==============================
    total_cost = 0

    for name, path in final_routes.items():
        if path is None:
            continue

        for i in range(1, len(path)):
            x1, y1, L1 = path[i - 1]
            x2, y2, L2 = path[i]

            if x1 == x2 and y1 == y2:
                total_cost += VIA_COST
            else:
                total_cost += WIRE_COST

        total_cost += 4  # pin entry/exit

    print("\nFINAL COST:", total_cost)

    # Save output
    out_path = os.path.join(LOG_DIR, "negotiated_output.py")
    with open(out_path, "w") as f:
        f.write("routes = ")
        f.write(str(final_routes))

    print("Output written to:", out_path)


if __name__ == "__main__":
    main()