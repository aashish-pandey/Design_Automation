# validator.py
from logs import output as data


original = data.original_data
outputdata = data.output_data


def validate():

    print("=== VALIDATING PLACEMENT ===")

    grid = outputdata["grid_size"]
    seen = set()

    # ---- check cells ----
    for name, info in outputdata["cells"].items():

        x, y = info["position"]

        # bounds check
        if not (0 <= x < grid and 0 <= y < grid):
            print("FAIL: out of bounds →", name, info["position"])
            return

        # overlap check
        if (x, y) in seen:
            print("FAIL: overlap at", (x, y))
            return

        seen.add((x, y))

    # ---- fixed cell check ----
    for name, info in original["cells"].items():

        if info["fixed"]:
            if info["position"] != outputdata["cells"][name]["position"]:
                print("FAIL: fixed cell moved →", name)
                return

    print("PLACEMENT VALID ✅")


validate()
