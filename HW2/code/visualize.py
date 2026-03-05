import matplotlib.pyplot as plt
import Rtest_100_250 as netlist   # change to your filename

data = netlist.data

grid_size = data['grid_size']
nets = data['nets']

plt.figure(figsize=(8, 8))
plt.xlim(0, grid_size)
plt.ylim(0, grid_size)
plt.gca().set_aspect('equal', adjustable='box')

plt.xticks(range(0, grid_size + 1, 10))
plt.yticks(range(0, grid_size + 1, 10))
plt.grid(True)

color_map = {
    'LOCAL': 'blue',
    'MEDIUM': 'orange',
    'LONG': 'red'
}

for net_name, info in nets.items():
    net_type = info['type']
    pins = info['pins']
    color = color_map.get(net_type, 'black')

    # plot pins
    for (x, y) in pins:
        plt.scatter(x, y, color=color, s=10)

    

# Legend
for net_type, color in color_map.items():
    plt.scatter([], [], color=color, label=net_type)

plt.legend()
plt.title("Netlist Pin Distribution")
plt.xlabel("X")
plt.ylabel("Y")

plt.show()