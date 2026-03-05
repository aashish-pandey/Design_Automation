import os
import math
from heapq import heappush, heappop

# ==============================
# DIRECT IMPORT (EDIT FILE NAME)
# ==============================

import Rtest_100_250 as netlist  # <-- change to your file name

data = netlist.data
grid_size = data["grid_size"]
nets_data = data["nets"]

# ==============================
# CONFIG
# ==============================

LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

# ==============================
# LAYER RULES
# ==============================

def is_vertical(layer):
    return layer % 2 == 0  # M2,4,6,8

# ==============================
# OCCUPANCY GRID
# ==============================

occupied = set()  # (x,y,layer)



def rip_up(net_name):
    global total_cost

    if routes[net_name] is None:
        return

    path, cost = routes[net_name]

    for p in path:
        if p in occupied:
            occupied.remove(p)

    total_cost -= cost
    routes[net_name] = None
# ==============================
# PATTERN ROUTER
# ==============================

def try_L(src, dst, order):
    x1, y1 = src
    x2, y2 = dst

    path = []
    path.append((x1, y1, 2))  # start at M2

    if order == "HV":
        # go to M3
        path.append((x1, y1, 3))
        step = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step, step):
            path.append((x, y1, 3))

        path.append((x2, y1, 2))
        step = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + step, step):
            path.append((x2, y, 2))

    else:  # VH
        step = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + step, step):
            path.append((x1, y, 2))

        path.append((x1, y2, 3))
        step = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step, step):
            path.append((x, y2, 3))

        path.append((x2, y2, 2))

    # remove duplicates
    cleaned = []
    for p in path:
        if not cleaned or cleaned[-1] != p:
            cleaned.append(p)

    # check occupancy
    for p in cleaned:
        if p in occupied:
            return None

    return cleaned

# ==============================
# BOUNDED DIJKSTRA
# ==============================

def neighbors(x, y, layer, bbox):
    xmin, xmax, ymin, ymax = bbox

    # wire
    if is_vertical(layer):
        for ny in (y - 1, y + 1):
            if xmin <= x <= xmax and ymin <= ny <= ymax:
                yield (x, ny, layer), 1
    else:
        for nx in (x - 1, x + 1):
            if xmin <= nx <= xmax and ymin <= y <= ymax:
                yield (nx, y, layer), 1

    # via
    if layer > 2:
        yield (x, y, layer - 1), 2
    if layer < 9:
        yield (x, y, layer + 1), 2


def dijkstra(src, dst, margin=5):
    x1, y1 = src
    x2, y2 = dst

    xmin = max(0, min(x1, x2) - margin)
    xmax = min(grid_size - 1, max(x1, x2) + margin)
    ymin = max(0, min(y1, y2) - margin)
    ymax = min(grid_size - 1, max(y1, y2) + margin)

    bbox = (xmin, xmax, ymin, ymax)

    start = (x1, y1, 2)
    goal_xy = (x2, y2)

    pq = []
    heappush(pq, (0, start))

    dist = {start: 0}
    parent = {}

    while pq:
        cost, u = heappop(pq)
        if u not in dist or cost != dist[u]:
            continue

        x, y, L = u

        if (x, y) == goal_xy and L == 2:
            path = [u]
            while u in parent:
                u = parent[u]
                path.append(u)
            path.reverse()
            return path

        for v, w in neighbors(x, y, L, bbox):
            if v in occupied:
                continue

            nx, ny, nL = v
            if not (0 <= nx < grid_size and 0 <= ny < grid_size):
                continue

            new_cost = cost + w
            if v not in dist or new_cost < dist[v]:
                dist[v] = new_cost
                parent[v] = u
                heappush(pq, (new_cost, v))

    return None




#=============================
#A STAR
# =============================

from heapq import heappush, heappop

def heuristic(x, y, L, goal_xy):
    gx, gy = goal_xy
    manhattan = abs(x - gx) + abs(y - gy)
    via_cost = 2 * abs(L - 2)   # must end at layer 2
    return manhattan + via_cost


def Astar(src, dst, margin=5):  # keeping same name/signature as requested
    x1, y1 = src
    x2, y2 = dst

    xmin = max(0, min(x1, x2) - margin)
    xmax = min(grid_size - 1, max(x1, x2) + margin)
    ymin = max(0, min(y1, y2) - margin)
    ymax = min(grid_size - 1, max(y1, y2) + margin)

    bbox = (xmin, xmax, ymin, ymax)

    start = (x1, y1, 2)
    goal_xy = (x2, y2)

    pq = []
    heappush(pq, (heuristic(x1, y1, 2, goal_xy), 0, start))

    g_cost = {start: 0}
    parent = {}

    while pq:
        f_cost, cost, u = heappop(pq)

        if u not in g_cost or cost != g_cost[u]:
            continue

        x, y, L = u

        if (x, y) == goal_xy and L == 2:
            path = [u]
            while u in parent:
                u = parent[u]
                path.append(u)
            path.reverse()
            return path

        for v, w in neighbors(x, y, L, bbox):
            if v in occupied:
                continue

            nx, ny, nL = v
            if not (0 <= nx < grid_size and 0 <= ny < grid_size):
                continue

            new_cost = cost + w

            if v not in g_cost or new_cost < g_cost[v]:
                g_cost[v] = new_cost
                parent[v] = u
                f_new = new_cost + heuristic(nx, ny, nL, goal_xy)
                heappush(pq, (f_new, new_cost, v))

    return None
# ==============================
# ROUTING
# ==============================

nets = []

for name, info in nets_data.items():
    (x1, y1), (x2, y2) = info["pins"]
    manh = abs(x1 - x2) + abs(y1 - y2)
    nets.append((name, (x1, y1), (x2, y2), manh))

# longest first
nets.sort(key=lambda x: x[3], reverse=False)

routes = {}
total_cost = 0
failed_nets = 0

for name, src, dst, _ in nets:

    path = try_L(src, dst, "HV")
    if not path:
        path = try_L(src, dst, "VH")

    # if not path:
    #     path = dijkstra(src, dst)
    if not path:
        path = Astar(src, dst)
    if not path:
        print("Failed:", name)
        failed_nets += 1
        routes[name] = None
        continue

    # commit
    for p in path:
        occupied.add(p)

    cost = 0
    for i in range(1, len(path)):
        x1, y1, L1 = path[i - 1]
        x2, y2, L2 = path[i]
        if x1 == x2 and y1 == y2:
            cost += 2
        else:
            cost += 1

    cost += 4  # M1->M2 + M2->M1

    routes[name] = (path, cost)
    total_cost += cost

# ==============================
# BUILD OUTPUT
# ==============================

output = {
    "meta": {
        "grid_size": grid_size,
        "layer_directions": {
            "M2": "V", "M3": "H",
            "M4": "V", "M5": "H",
            "M6": "V", "M7": "H",
            "M8": "V", "M9": "H"
        },
        "total_cost": total_cost
    },
    "nets": {}
}

for name, src, dst, _ in nets:
    (x1, y1), (x2, y2) = nets_data[name]["pins"]

    if routes[name] is None:
        output["nets"][name] = {
            "pins": [(x1, y1), (x2, y2)],
            "segments": [],
            "cost": 0
        }
        continue

    path, cost = routes[name]

    segments = []
    segments.append({"start": (x1, y1, "M1"), "end": (x1, y1, "M2")})

    for i in range(1, len(path)):
        x1, y1, L1 = path[i - 1]
        x2, y2, L2 = path[i]
        segments.append({
            "start": (x1, y1, f"M{L1}"),
            "end": (x2, y2, f"M{L2}")
        })

    segments.append({"start": (x2, y2, "M2"), "end": (x2, y2, "M1")})

    output["nets"][name] = {
        "pins": [(x1, y1), (x2, y2)],
        "segments": segments,
        "cost": cost
    }

# write file
out_path = os.path.join(LOG_DIR, "route_output.py")
with open(out_path, "w") as f:
    f.write("data = ")
    f.write(str(output))

print("Routing complete.")
print("Total cost:", total_cost)
print("Failed nets:", failed_nets)
print("Output written to:", out_path)