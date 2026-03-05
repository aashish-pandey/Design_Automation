import math

x_data = [0,1,2,3,4]
y_data = [5,3.2,2.1,1.4,0.9]

def model(x,a,b):
    return a * math.exp(-b*x)

a = 5
b = 0.5

width = 700
height = 500
margin = 60

xmin, xmax = min(x_data), max(x_data)
ymin, ymax = min(y_data), max(y_data)

def scale_x(x):
    return margin + (x-xmin)/(xmax-xmin)*(width-2*margin)

def scale_y(y):
    return height - (margin + (y-ymin)/(ymax-ymin)*(height-2*margin))


svg = []

svg.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">')

# white background
svg.append(f'<rect width="100%" height="100%" fill="white"/>')

# scatter points (circles)
for x,y in zip(x_data,y_data):
    cx = scale_x(x)
    cy = scale_y(y)
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="blue"/>')

# fitted curve
curve_points = []
for i in range(200):
    x = xmin + (xmax-xmin)*i/199
    y = model(x,a,b)
    curve_points.append(f"{scale_x(x)},{scale_y(y)}")

svg.append(
    f'<polyline points="{" ".join(curve_points)}" '
    'fill="none" stroke="red" stroke-width="2"/>'
)

# stars on fitted points
for x in x_data:
    y = model(x,a,b)
    cx = scale_x(x)
    cy = scale_y(y)

    svg.append(f'<text x="{cx}" y="{cy}" '
               f'font-size="18" text-anchor="middle" '
               f'dominant-baseline="middle" fill="black">*</text>')

svg.append("</svg>")

with open("curve_plot.svg","w") as f:
    f.write("\n".join(svg))