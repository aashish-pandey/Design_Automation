import sys
import os
import importlib

# ===============================
# CONFIG
# ===============================

INPUT_NETLIST = "Rtest_100_250"     # change if needed
OUTPUT_FILE = "log.negotiated_output"      # use dot notation

# ===============================
# IMPORT INPUT + OUTPUT
# ===============================

input_module = importlib.import_module(INPUT_NETLIST)
input_data = input_module.data

output_module = importlib.import_module(OUTPUT_FILE)
output_data = output_module.data

grid_size = input_data["grid_size"]

# ===============================
# LAYER RULES
# ===============================

def is_vertical(layer):
    return layer % 2 == 0

def is_horizontal(layer):
    return layer % 2 == 1

# ===============================
# VALIDATION
# ===============================

errors = 0
global_used_resources = set()

def error(msg):
    global errors
    print("ERROR:", msg)
    errors += 1

# -------------------------------
# 1. Check all nets exist
# -------------------------------

for net in input_data["nets"]:
    if net not in output_data["nets"]:
        error(f"Missing net in output: {net}")

# -------------------------------
# 2. Validate each net
# -------------------------------

for net_name, net_info in output_data["nets"].items():

    if net_name not in input_data["nets"]:
        error(f"Extra net in output: {net_name}")
        continue

    segments = net_info["segments"]
    reported_cost = net_info["cost"]

    if not segments:
        error(f"No route for net {net_name}")
        continue

    # Per-net tracking (to avoid self-overlap false positives)
    current_net_resources = set()

    # Check first segment
    first = segments[0]
    if not (first["start"][2] == "M1" and first["end"][2] == "M2"):
        error(f"{net_name}: First segment not M1->M2")

    # Check last segment
    last = segments[-1]
    if not (last["start"][2] == "M2" and last["end"][2] == "M1"):
        error(f"{net_name}: Last segment not M2->M1")

    prev_end = None
    computed_cost = 0

    for seg in segments:

        start = seg["start"]
        end = seg["end"]

        x1, y1, L1 = start
        x2, y2, L2 = end

        # continuity
        if prev_end and prev_end != start:
            error(f"{net_name}: Disconnected segment")

        L1_int = int(L1[1:])
        L2_int = int(L2[1:])

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        dL = abs(L2_int - L1_int)

        # -------------------
        # VIA
        # -------------------
        if dx == 0 and dy == 0 and dL == 1:
            computed_cost += 2

        # -------------------
        # WIRE
        # -------------------
        elif dL == 0:
            if dx > 0 and dy == 0:
                if not is_horizontal(L1_int):
                    error(f"{net_name}: Horizontal wire on vertical layer")
                computed_cost += dx
            elif dy > 0 and dx == 0:
                if not is_vertical(L1_int):
                    error(f"{net_name}: Vertical wire on horizontal layer")
                computed_cost += dy
            else:
                error(f"{net_name}: Invalid wire movement")
        else:
            error(f"{net_name}: Invalid segment")

        # -------------------
        # Bounds check (ignore M1)
        # -------------------
        if L2_int != 1:
            if not (0 <= x2 < grid_size and 0 <= y2 < grid_size):
                error(f"{net_name}: Out of bounds at {(x2,y2,L2_int)}")

        # -------------------
        # Overlap check
        # -------------------
        if L2_int != 1:
            resource = (x2, y2, L2_int)

            # If another net already used it → error
            if resource in global_used_resources and resource not in current_net_resources:
                error(f"{net_name}: Overlap at {resource}")

            current_net_resources.add(resource)
            global_used_resources.add(resource)

        prev_end = end

    if computed_cost != reported_cost:
        error(f"{net_name}: Cost mismatch (reported {reported_cost}, computed {computed_cost})")

# -------------------------------
# Final Result
# -------------------------------

if errors == 0:
    print("\nVALIDATION PASSED ✓")
else:
    print(f"\nVALIDATION FAILED with {errors} errors.")