import os
import math
from heapq import heappush, heappop
from collections import defaultdict

# ==============================
# IMPORT NETLIST (same style as yours)
# ==============================
import Rtest_100_500 as netlist   # <-- change here when needed

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

CAPACITY = 1                 # cell capacity (detailed routing)

MAX_ITERS = 30

ALPHA_PRESENT = 4.0
BETA_HISTORY = 1.0
HISTORY_INCREMENT = 1.0

MARGIN = 20                  # detailed bbox margin (in cells)

# ------------------------------
# HIERARCHICAL (GLOBAL/LOCAL)
# ------------------------------
TILE_SIZE = 20               # e.g., 100x100 grid -> 5x5 tiles
TILE_MARGIN = 1              # expand tile corridor by this many tiles for detailed routing
TILE_CAPACITY = 5            # how many global nets can "share" a tile before overflow (tune this)

ALPHA_TILE_PRESENT = 3.0     # penalty for tile overflow in global router
BETA_TILE_HISTORY = 1.0
TILE_HISTORY_INCREMENT = 1.0

LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

# ==============================
# LAYER RULES
# ==============================
def is_vertical(layer):
    return layer % 2 == 0


# ==============================
# TILE HELPERS
# ==============================
def num_tiles():
    return math.ceil(grid_size / TILE_SIZE)

def tile_of(x, y):
    return (x // TILE_SIZE, y // TILE_SIZE)

def tile_bbox(tx, ty):
    xmin = tx * TILE_SIZE
    xmax = min(grid_size - 1, (tx + 1) * TILE_SIZE - 1)
    ymin = ty * TILE_SIZE
    ymax = min(grid_size - 1, (ty + 1) * TILE_SIZE - 1)
    return (xmin, xmax, ymin, ymax)

def clamp_bbox(bbox):
    xmin, xmax, ymin, ymax = bbox
    xmin = max(0, xmin)
    ymin = max(0, ymin)
    xmax = min(grid_size - 1, xmax)
    ymax = min(grid_size - 1, ymax)
    return (xmin, xmax, ymin, ymax)

def bbox_from_tile_path(tile_path, tile_margin=TILE_MARGIN):
    if not tile_path:
        return (0, grid_size - 1, 0, grid_size - 1)

    ntx = num_tiles()

    xs = [t[0] for t in tile_path]
    ys = [t[1] for t in tile_path]

    txmin = max(0, min(xs) - tile_margin)
    txmax = min(ntx - 1, max(xs) + tile_margin)
    tymin = max(0, min(ys) - tile_margin)
    tymax = min(ntx - 1, max(ys) + tile_margin)

    xmin = txmin * TILE_SIZE
    xmax = min(grid_size - 1, (txmax + 1) * TILE_SIZE - 1)
    ymin = tymin * TILE_SIZE
    ymax = min(grid_size - 1, (tymax + 1) * TILE_SIZE - 1)

    return (xmin, xmax, ymin, ymax)

def bbox_from_pins(src, dst, margin=MARGIN):
    x1, y1 = src
    x2, y2 = dst
    xmin = max(0, min(x1, x2) - margin)
    xmax = min(grid_size - 1, max(x1, x2) + margin)
    ymin = max(0, min(y1, y2) - margin)
    ymax = min(grid_size - 1, max(y1, y2) + margin)
    return (xmin, xmax, ymin, ymax)


# ==============================
# SEGMENT GENERATION (pattern routing)
# ==============================
def segment(x1, y1, x2, y2, layer):
    path = []
    if x1 == x2:
        step = 1 if y2 > y1 else -1
        for y in range(y1, y2 + step, step):
            path.append((x1, y, layer))
    elif y1 == y2:
        step = 1 if x2 > x1 else -1
        for x in range(x1, x2 + step, step):
            path.append((x, y1, layer))
    else:
        return None
    return path


# ==============================
# PATH VALIDATION (STRICT)
# - Must stay inside bbox
# - Must not overflow usage
# - Must not touch history>0
# ==============================
def path_valid(path, usage, history, bbox):
    xmin, xmax, ymin, ymax = bbox

    for node in path:
        x, y, L = node

        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            return False

        if not (0 <= x < grid_size and 0 <= y < grid_size):
            return False

        if usage[node] >= CAPACITY:
            return False

        if history[node] > 0:
            return False

    return True


# ==============================
# L PATTERN ROUTER (inside bbox)
# ==============================
def L_route(src, dst, usage, history, bbox):
    x1, y1 = src
    x2, y2 = dst
    layer = LMIN

    # horizontal then vertical
    p1 = segment(x1, y1, x2, y1, layer)
    p2 = segment(x2, y1, x2, y2, layer)
    if p1 and p2:
        path = p1 + p2[1:]
        if path_valid(path, usage, history, bbox):
            return path

    # vertical then horizontal
    p1 = segment(x1, y1, x1, y2, layer)
    p2 = segment(x1, y2, x2, y2, layer)
    if p1 and p2:
        path = p1 + p2[1:]
        if path_valid(path, usage, history, bbox):
            return path

    return None


# ==============================
# Z PATTERN ROUTER (inside bbox)
# ==============================
def Z_route(src, dst, usage, history, bbox):
    x1, y1 = src
    x2, y2 = dst
    layer = LMIN

    # try intermediate X
    for xm in range(min(x1, x2) + 1, max(x1, x2)):
        p1 = segment(x1, y1, xm, y1, layer)
        p2 = segment(xm, y1, xm, y2, layer)
        p3 = segment(xm, y2, x2, y2, layer)
        if p1 and p2 and p3:
            path = p1 + p2[1:] + p3[1:]
            if path_valid(path, usage, history, bbox):
                return path

    # try intermediate Y
    for ym in range(min(y1, y2) + 1, max(y1, y2)):
        p1 = segment(x1, y1, x1, ym, layer)
        p2 = segment(x1, ym, x2, ym, layer)
        p3 = segment(x2, ym, x2, y2, layer)
        if p1 and p2 and p3:
            path = p1 + p2[1:] + p3[1:]
            if path_valid(path, usage, history, bbox):
                return path

    return None


# ==============================
# PATTERN ROUTER (L + Z)
# ==============================
def pattern_route(src, dst, usage, history, bbox):
    path = L_route(src, dst, usage, history, bbox)
    if path:
        return path

    path = Z_route(src, dst, usage, history, bbox)
    if path:
        return path

    return None


# ==============================
# DETAILED NEIGHBOR GENERATION (A*)
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
# DETAILED HEURISTIC
# ==============================
def heuristic(x, y, L, goal_xy):
    gx, gy = goal_xy
    manhattan = abs(x - gx) + abs(y - gy)
    via_back = VIA_COST * abs(L - LMIN)
    return manhattan + via_back


# ==============================
# DETAILED CONGESTION COST
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
# DETAILED A* (uses explicit bbox)
# ==============================
def astar_route(src, dst, usage, history, bbox):
    x1, y1 = src
    x2, y2 = dst

    bbox = clamp_bbox(bbox)
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
# GLOBAL (TILE) ROUTER
# ==============================
def tile_neighbors(tx, ty):
    n = num_tiles()
    for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
        nx, ny = tx + dx, ty + dy
        if 0 <= nx < n and 0 <= ny < n:
            yield (nx, ny)

def tile_heuristic(t, goal):
    tx, ty = t
    gx, gy = goal
    return abs(tx - gx) + abs(ty - gy)

def tile_step_cost(tile, tile_usage, tile_history):
    # Cost to "occupy" this tile one more time
    predicted = tile_usage[tile] + 1
    overflow = max(0, predicted - TILE_CAPACITY)
    return 1 + ALPHA_TILE_PRESENT * overflow + BETA_TILE_HISTORY * tile_history[tile]

def tile_astar(tile_src, tile_dst, tile_usage, tile_history):
    start = tile_src
    goal = tile_dst

    pq = []
    heappush(pq, (tile_heuristic(start, goal), 0, start))

    g_cost = {start: 0}
    parent = {}

    while pq:
        f, cost, u = heappop(pq)
        if cost != g_cost.get(u, None):
            continue

        if u == goal:
            path = [u]
            while u in parent:
                u = parent[u]
                path.append(u)
            path.reverse()
            return path

        for v in tile_neighbors(*u):
            step = tile_step_cost(v, tile_usage, tile_history)
            new_cost = cost + step

            if new_cost < g_cost.get(v, float("inf")):
                g_cost[v] = new_cost
                parent[v] = u
                f_new = new_cost + tile_heuristic(v, goal)
                heappush(pq, (f_new, new_cost, v))

    return None


# ==============================
# COST (wire/via + pin overhead)
# ==============================
def path_cost(path):
    if not path or len(path) < 2:
        return float("inf")

    cost = 0
    for i in range(1, len(path)):
        x1, y1, L1 = path[i - 1]
        x2, y2, L2 = path[i]
        if x1 == x2 and y1 == y2:
            cost += VIA_COST
        else:
            cost += WIRE_COST

    cost += 4
    return cost


# ==============================
# MAIN HIERARCHICAL ENGINE
# - Route GLOBAL nets first (tile path -> detailed inside corridor)
# - Then route LOCAL nets (inside its tile bbox)
# - Per-net method: Pattern -> A*
# - Negotiated iterations on BOTH:
#     (1) detailed congestion history
#     (2) tile congestion history
# ==============================
def main():
    # Build net list with classification (global/local)
    nets = []
    global_nets = []
    local_nets = []

    for name, info in nets_data.items():
        (x1, y1), (x2, y2) = info["pins"]
        src = (x1, y1)
        dst = (x2, y2)
        manh = abs(x1 - x2) + abs(y1 - y2)

        t1 = tile_of(x1, y1)
        t2 = tile_of(x2, y2)
        is_global = (t1 != t2)

        item = (name, src, dst, manh, t1, t2, is_global)
        nets.append(item)

        if is_global:
            global_nets.append(item)
        else:
            local_nets.append(item)

    # Sort within each group (shorter first is usually easier)
    global_nets.sort(key=lambda x: x[3])
    local_nets.sort(key=lambda x: x[3])

    history = defaultdict(float)          # detailed history per (x,y,layer)
    tile_history = defaultdict(float)     # global history per tile (tx,ty)

    final_routes = {}
    final_tile_routes = {}

    for iteration in range(1, MAX_ITERS + 1):
        print(f"\n=== Iteration {iteration} ===")

        usage = defaultdict(int)          # detailed usage per (x,y,layer)
        tile_usage = defaultdict(int)     # global usage per tile
        routes = {}
        tile_routes = {}
        failed = 0

        # --------------------------
        # 1) Route GLOBAL nets first
        # --------------------------
        for name, src, dst, manh, t1, t2, is_global in global_nets:
            # tile-level path first
            tile_path = tile_astar(t1, t2, tile_usage, tile_history)
            if tile_path is None:
                # fallback: naive straight tile bbox corridor (very simple fallback)
                tile_path = [t1, t2]

            tile_routes[name] = tile_path

            # build corridor bbox from tile_path
            bbox = bbox_from_tile_path(tile_path, tile_margin=TILE_MARGIN)

            # Pattern -> A*
            path = pattern_route(src, dst, usage, history, bbox)
            if path is None:
                path = astar_route(src, dst, usage, history, bbox)

            if path is None:
                failed += 1
                routes[name] = None
                continue

            routes[name] = path

            # update detailed usage
            for node in path:
                usage[node] += 1

            # update tile usage (coarse reservation)
            for t in tile_path:
                tile_usage[t] += 1

        # --------------------------
        # 2) Route LOCAL nets second
        # --------------------------
        for name, src, dst, manh, t1, t2, is_global in local_nets:
            # local bbox = its tile bbox expanded by MARGIN (cells)
            tx, ty = t1
            tb = tile_bbox(tx, ty)
            bbox = clamp_bbox((
                tb[0] - MARGIN, tb[1] + MARGIN,
                tb[2] - MARGIN, tb[3] + MARGIN
            ))

            path = pattern_route(src, dst, usage, history, bbox)
            if path is None:
                path = astar_route(src, dst, usage, history, bbox)

            if path is None:
                failed += 1
                routes[name] = None
                continue

            routes[name] = path
            for node in path:
                usage[node] += 1

        # --------------------------
        # 3) Check DETAILED congestion
        # --------------------------
        overflow_nodes = []
        total_overflow = 0
        for node, u in usage.items():
            if u > CAPACITY:
                overflow = u - CAPACITY
                total_overflow += overflow
                overflow_nodes.append(node)

        # --------------------------
        # 4) Check TILE congestion (GLOBAL)
        # --------------------------
        overflow_tiles = []
        total_tile_overflow = 0
        for t, u in tile_usage.items():
            if u > TILE_CAPACITY:
                overflow = u - TILE_CAPACITY
                total_tile_overflow += overflow
                overflow_tiles.append(t)

        print("Failed nets:", failed)
        print("Total overflow (detailed):", total_overflow)
        print("Total overflow (tiles):", total_tile_overflow)

        # Converged if everything is clean
        if failed == 0 and total_overflow == 0 and total_tile_overflow == 0:
            print("Routing converged successfully.")
            final_routes = routes
            final_tile_routes = tile_routes
            break

        # Update detailed history penalties
        for node in overflow_nodes:
            history[node] += HISTORY_INCREMENT

        # Update tile history penalties
        for t in overflow_tiles:
            tile_history[t] += TILE_HISTORY_INCREMENT

        final_routes = routes
        final_tile_routes = tile_routes

    # ==============================
    # Final cost
    # ==============================
    total_cost = 0
    for name, path in final_routes.items():
        if path is None:
            continue
        total_cost += path_cost(path)

    print("\nFINAL COST:", total_cost)

    # Save detailed routes
    out_path = os.path.join(LOG_DIR, "hierarchical_output.py")
    with open(out_path, "w") as f:
        f.write("routes = ")
        f.write(str(final_routes))

    # Save tile routes (debug/visualization help)
    out_tile_path = os.path.join(LOG_DIR, "hierarchical_tile_output.py")
    with open(out_tile_path, "w") as f:
        f.write("tile_routes = ")
        f.write(str(final_tile_routes))

    print("Output written to:", out_path)
    print("Tile output written to:", out_tile_path)


if __name__ == "__main__":
    main()