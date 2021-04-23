# %%

import math
import numpy as np
import matplotlib.pyplot as plt

# Reasonable step sizes for computing offsets
MIN_STEP_SIZE = 5 # 5 deg
DEFAULT_DISTANCE_M = 64 # coresponds to the typical view distance in minecraft in meters

def gen_1_point(max_distance=DEFAULT_DISTANCE_M):
    points = []
    # 1 point (x, y, distance)
    points.append((0, 0, max_distance))
    return points

def get_grid_of_points(num_x, num_y, x_range_deg=30, y_range_deg=10, max_distance=DEFAULT_DISTANCE_M):
    """
    Generate a grid of points centered around the origin
    """
    points = []
    # Convert deg to rad
    x_range = 0.5 * x_range_deg * math.pi / 180
    y_range = 0.5 * y_range_deg * math.pi / 180
    step_x = 2 * x_range / (num_x - 1)
    step_y = 2 * y_range / (num_y - 1)
    for i in range(num_x):
        for j in range(num_y):
            x = -x_range + step_x * i
            y = -y_range + step_y * j
            points.append((x, y, max_distance))
    return points

def get_square_grid_of_points(num,range_deg=30, max_distance=DEFAULT_DISTANCE_M):
    """
    Generate a grid of points centered around the origin
    """
    points = []
    # Convert deg to rad
    half_range = 0.5 * range_deg * math.pi / 180
    step = 2 * half_range / (num - 1)
    for i in range(num):
        for j in range(num):
            x = -half_range + step * i
            y = -half_range + step * j
            points.append((x, y, max_distance))
    return points

def get_cross_hatch_of_points(num_segments, fov_deg=30, max_distance=DEFAULT_DISTANCE_M,):
    """
    A cross hatch of points
    points are represented by an x, y offset

    """
    points = []
    step = fov_deg * math.pi / 180 / num_segments
    for i in range(num_segments):
        x = i * step
        y = i * step
        points.append((x, y, max_distance))
        points.append((-x, y, max_distance))
        points.append((x, -y, max_distance))
        points.append((-x, -y, max_distance))
    return points

def get_horizontal_line_of_points(num_points=4, range_deg=30, offset=0, max_distance=DEFAULT_DISTANCE_M):
    """
    A horizontal line consisting of num_points points with range +- range_deg
    points are represented by an x, y offset and centered around the origin
    """
    points = []
    half_range = 0.5 * range_deg * math.pi / 180
    step = 2 * half_range / (num_points - 1)
    for i in range(num_points):
        x = -half_range + i * step
        y = offset
        points.append((x, y, max_distance))
    return points


def get_vertical_line_of_points(num_points=4, range_deg=10, offset=0, max_distance=DEFAULT_DISTANCE_M):
    """
    A vertical line consisting of num_points points with range +- range_deg
    points are represented by an x, y offset and centered around the origin
    """
    points = []
    half_range = 0.5 * range_deg * math.pi / 180
    step = 2 * half_range / (num_points - 1)
    for i in range(num_points):
        x = offset
        y = -half_range + i * step
        points.append((x, y, max_distance))
    return points


def get_circle_of_points(fov_deg=30, num_points=8, max_distance=DEFAULT_DISTANCE_M, ):
    """
    A circle of points
    points are represented by an x, y offset

    """
    points = []
    radius = fov_deg * math.pi / 180 / 2
    for i in range(num_points):
        x = radius * math.sin(math.radians(360 / num_points * i))
        y = radius * math.cos(math.radians(360 / num_points * i))
        points.append((x, y, max_distance))
    return points

def get_spiral_of_points(num_points=8, max_distance=DEFAULT_DISTANCE_M):
    """
    Define a spiral function to generate a spiral of points starting at the origin
    and going counter-clockwise.
    Must use trigonometric functions to generate x and y values
    """
    points = []
    step = MIN_STEP_SIZE * math.pi / 180
    for i in range(num_points):
        r = i * step
        x = r * math.cos(2 * math.pi * i / num_points)
        y = r * math.sin(2 * math.pi * i / num_points)
        points.append((x, y, max_distance))
    return points

def get_spiral_of_points_reverse(num_points=8, max_distance=DEFAULT_DISTANCE_M):
    """
    Define a spiral function to generate a spiral of points from the origin
    going clockwise.
    Must use trigonometric functions to generate x and y values
    """
    points = []
    step = MIN_STEP_SIZE * math.pi / 180
    for i in range(num_points):
        r = i * step
        x = -r * math.cos(2 * math.pi * i / num_points)
        y = -r * math.sin(2 * math.pi * i / num_points)
        points.append((x, y, max_distance))
    return points

def get_4_spirals_of_points(num_points=8, step_size=None, max_distance=DEFAULT_DISTANCE_M):
    """
    Define a spiral function to generate a spiral of points from the origin
    going clockwise.
    Must use trigonometric functions to generate x and y values
    """
    points = []
    step = MIN_STEP_SIZE if step_size is None else step_size
    step *= math.pi / 180
    for i in range(num_points):
        r = i * step
        x = -r * math.cos(2 * math.pi * i / num_points)
        y = -r * math.sin(2 * math.pi * i / num_points)
        points.append((x, y, max_distance))
        points.append((x, -y, max_distance))
        points.append((-x, y, max_distance))
        points.append((-x, -y, max_distance))
    return points

def remove_duplicate_points(points):
    """
    Remove duplicate points from a list of points.
    """
    unique_points = []
    for p in points:
        if p not in unique_points:
            unique_points.append(p)
    return unique_points

def get_foveated_points(points, fov_deg=30):
    """
    Generate a list of points that are within the field of view of the camera
    """
    fov_rad = 0.5 * fov_deg * math.pi / 180
    fov_points = []
    for p in points:
        x, y, d = p
        if x**2 + y**2 <= fov_rad**2:
            fov_points.append(p)
    return fov_points



def gen_halo_of_points(max_distance=DEFAULT_DISTANCE_M, num_points=8):
    """
    Generates a halo of points around the origin
    points go from -pi to pi
    """
    points = []
    for step in np.linspace(start=-3.14159, stop=3.14159, num=num_points, endpoint=False):
        x = 0
        y = step
        points.append((x, y, max_distance))
    return points

def visualize_points(points):
    """
    Visualize a list of points.
    """
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    plt.scatter(x, y, s=1, c='b', label="Points", marker="x")
    plt.legend(loc="upper left")
    plt.show()
    plt.close()

# %%
if __name__ == '__main__':

    rect = get_square_grid_of_points(5,30)
    visualize_points(rect)

    fov_rect = get_foveated_points(rect, fov_deg=30)
    visualize_points(fov_rect)

    cross = get_cross_hatch_of_points(num_segments=4, fov_deg=30)
    visualize_points(cross)

    circ = get_circle_of_points(fov_deg=30, num_points=8)
    visualize_points(circ)

    spiral = get_spiral_of_points(num_points=8, max_distance=DEFAULT_DISTANCE_M)
    visualize_points(spiral)

    all_spiral = get_4_spirals_of_points(num_points=8, max_distance=DEFAULT_DISTANCE_M)
    visualize_points(all_spiral)

    all = remove_duplicate_points(rect + fov_rect + cross + circ + spiral + all_spiral)
    visualize_points(all)

# %%
