from skimage import color
import numpy as np
from scipy import signal
from scipy.spatial import ConvexHull
from scipy.spatial.distance import cdist
import math
import higra as hg
import artificial_info as ai


# Turn Seconds input into String with Days, Hours, Minutes and Seconds
def convert_seconds_to_string(seconds):
    seconds = round(seconds, 0)
    output = "["
    if seconds >= 60:
        minutes = seconds // 60
        seconds = seconds % 60
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            if hours >= 24:
                days = hours // 24
                hours = hours % 24
                output = str(int(days)) + "d:"
            output += str(int(hours)) + "h:"
        output += str(int(minutes)) + "m:"
    output += str(int(seconds)) + "s"
    return colored_string(output + "]", "black")


def colored_string(text, c):
    if c == "red":
        return "\033[91m" + text + "\033[0m"
    if c == "green":
        return "\033[92m" + text + "\033[0m"
    if c == "yellow":
        return "\033[93m" + text + "\033[0m"
    if c == "blue":
        return "\033[94m" + text + "\033[0m"
    if c == "purple":
        return "\033[95m" + text + "\033[0m"
    if c == "black":
        return "\033[47m\033[30m" + text + "\033[0m"


def create_graph(mds_image, size):
    graph = hg.get_4_adjacency_graph(size)
    grad_img = None
    if ai.CIRCULAR:
        stiched_mds_image = np.hstack((mds_image,) * 3)
        stitched_grad_img = gradient_image(stiched_mds_image)

        stitched_grad_img = np.transpose(stitched_grad_img, (1,2,0))
        stitched_grad_img = np.linalg.norm(stitched_grad_img, axis=2)
        grad_img = stitched_grad_img[:, size[1]:2 * size[1]]

        sources = np.arange(0, graph.num_vertices(), size[1])
        targets = np.arange(size[1] - 1, graph.num_vertices(), size[1])
        graph.add_edges(sources, targets)
    if ai.SOBEL:
        if grad_img is None:
            grad_img = gradient_image(mds_image)
            grad_img = np.transpose(grad_img, (1,2,0))
            grad_img = np.linalg.norm(grad_img, axis=2)
        edge_weights = hg.weight_graph(graph, grad_img, hg.WeightFunction.mean)
    else:
        edge_weights = hg.weight_graph(graph, mds_image, hg.WeightFunction.L2)
    tree, altitudes = hg.watershed_hierarchy_by_area(graph, edge_weights)
    return tree, altitudes


def concatenate_timelines(data):
    data_concatenated = np.empty((0, 0))
    for i in range(len(data)):
        timeline = data[i]
        timeline = timeline.reshape((timeline.shape[0] * timeline.shape[1], timeline.shape[2]))
        if data_concatenated.shape == (0, 0):
            data_concatenated = timeline
        else:
            data_concatenated = np.append(data_concatenated, timeline, axis=1)
    return data_concatenated


# Normalize with the same scaling factor in all directions
def normalize_point(points):
    points_min_vector = np.min(points)
    points_max_vector = np.max(points)
    points_normalized = (points - points_min_vector) / (points_max_vector - points_min_vector)
    return points_normalized


# Identify most distant points
# https://stackoverflow.com/questions/31667070/max-distance-between-2-points-in-a-data-set-and-identifying-the-points
def bestpair(points):
    hull = ConvexHull(points)
    hullpoints = points[hull.vertices, :]
    # Naive way of finding the best pair in O(H^2) time if H is number of points on hull
    hdist = cdist(hullpoints, hullpoints, metric='euclidean')
    # Get the farthest apart points
    bestpair = np.unravel_index(hdist.argmax(), hdist.shape)
    return hullpoints[bestpair[0]], hullpoints[bestpair[1]]


# Puts maximum distance on diagonal
def rotate_points(points):
    p1, p2 = bestpair(points)
    # Get the angle between the points and the diagonal
    vec = p2 - p1
    vec_norm = vec/np.linalg.norm(vec)
    # Rotate around vector perpendicular to the other two
    direction = np.array([1, 1, 1])/np.sqrt(3)
    n = np.cross(vec_norm, direction)
    n = n/np.linalg.norm(n)
    rot_angle = math.acos(np.dot(vec_norm, direction))
    cosA = math.cos(rot_angle)
    sinA = math.sin(rot_angle)
    rot_mat = np.array([[n[0]**2*(1-cosA)+cosA, n[0]*n[1]*(1-cosA)-n[2]*sinA, n[0]*n[2]*(1-cosA)+n[1]*sinA],
                        [n[1]*n[0]*(1-cosA)+n[2]*sinA, n[1]**2*(1-cosA)+cosA, n[1]*n[2]*(1-cosA)-n[0]*sinA],
                        [n[2]*n[0]*(1-cosA)-n[1]*sinA, n[2]*n[1]*(1-cosA)+n[0]*sinA, n[2]**2*(1-cosA)+cosA]])
    # Rotate points:
    points_rot = np.empty(points.shape)
    for i in range(len(points)):
        points_rot[i] = np.matmul(rot_mat, points[i])
    return points_rot


# Use the sobel operator to create a gradient image
def gradient_image(image_data):
    gradient_image = []
    sobel = np.array([[-1, 0, 1], [-4, 0, 4], [-1, 0, 1]])
    for i in range(0, image_data.shape[2]):
        chan = image_data[..., i]
        dx = np.abs(signal.convolve2d(chan, sobel, 'same'))
        dy = np.abs(signal.convolve2d(chan, sobel.T, 'same'))
        for row in range(dx.shape[0]):
            p = 1 / (dx.shape[0] - 1) * row  # scale btwn 0 and 1 pi
            sin = np.sin(p * np.pi)
            dx[row] = dx[row] * sin
        gradient_image.append(dx + dy)
    return np.array(gradient_image)


# Create mds image in L*a*b* space
def mds_image(mds_points, img_shape):
    mds_points = rotate_points(mds_points)
    mds_points = normalize_point(mds_points)
    mds_image = np.reshape(mds_points, (*img_shape, mds_points.shape[-1]))
    mds_image[:, :, 0] = mds_image[:, :, 0] * 100
    mds_image[:, :, 1] = mds_image[:, :, 1] * 100 - 50
    mds_image[:, :, 2] = mds_image[:, :, 2] * 100 - 50
    mds_image = color.lab2rgb(mds_image)
    return mds_image


# Create mds image in RGB space
def mds_rgb_image(mds_points, img_shape):
    mds_points = rotate_points(mds_points)
    mds_points = normalize_point(mds_points)
    mds_image = np.reshape(mds_points, (*img_shape, mds_points.shape[-1]))
    return mds_image


# Create mds image in HSV space
def mds_hsv_image(mds_points, img_shape):
    mds_points = rotate_points(mds_points)
    mds_points = normalize_point(mds_points)
    mds_image = np.reshape(mds_points, (*img_shape, mds_points.shape[-1]))
    mds_image[:, :, 0] = mds_image[:, :, 0]
    mds_image[:, :, 1] = mds_image[:, :, 1]
    mds_image[:, :, 2] = mds_image[:, :, 2]
    mds_image = color.hsv2rgb(mds_image)
    return mds_image


# Height for node in dendrogram tree
def get_height(segs, node, height):
    m = height
    if not segs[node].is_leaf:
        for c in segs[node].children:
            m = max(m, get_height(segs, c, height))
    return m + 1


# Width for node in dendrogram tree
def get_width(segs, node, width):
    m = width
    if segs[node].is_leaf:
        return width + 1
    else:
        for c in segs[node].children:
            m = m + get_width(segs, c, width)
    return m


# get root of dendrogram tree
def get_root(segs, node):
    if segs[node].parent != -1:
        get_root(segs, segs[node].parent)
    return node
