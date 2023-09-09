import logging

import segment as s
import numpy as np
import time
import artificial_info as ai
import utils as u

# -------------------------
#        Functions
# -------------------------


def calculate_hull(segment_points):
    clusters_points_list, extreme_values_list = find_clusters(segment_points)
    hulls = []
    polygons = []
    for i in range(len(clusters_points_list)):
        hulls, polygons = (create_hull(clusters_points_list[i], extreme_values_list[i], hulls, polygons))
    return hulls, polygons


# finds clusters in a list of points
def find_clusters(points):
    clusters_points_list = []
    extreme_values_list = []

    # create 2d array, where segment points are marked with a 1
    check_array = np.zeros((ai.SHAPE[2], ai.SHAPE[1]))
    for point in points:
        check_array[point[0], point[1]] = 1

    # find clusters
    current_point = points[0]
    backtrack_index = 0
    current_cluster = []
    current_extreme_values = [current_point[0], current_point[1], current_point[0], current_point[1]]
    while len(points) > 0:
        x = current_point[0]
        y = current_point[1]
        if [x, y] in points: # add point only if it is still in points, otherwise its backtracked to and no need to add it
            current_cluster.append([x, y])
            points.remove([x, y])
            check_array[x, y] = 0

        # check if there are adjacent neighbors
        if x > 0 and check_array[x - 1, y] == 1:  # left
            current_point = [x - 1, y]
            backtrack_index = 0
        elif x < check_array.shape[0] - 1 and check_array[x + 1, y] == 1:  # right
            current_point = [x + 1, y]
            backtrack_index = 0
        elif y > 0 and check_array[x, y - 1] == 1:  # top
            current_point = [x, y - 1]
            backtrack_index = 0
        elif y < check_array.shape[1] - 1 and check_array[x, y + 1] == 1:  # bottom
            current_point = [x, y + 1]
            backtrack_index = 0
        else:
            backtrack_index += 1
            if (len(current_cluster) - backtrack_index) != -1:
                current_point = current_cluster[len(current_cluster) - backtrack_index]

        # check for new extreme values
        if x < current_extreme_values[0]:  # left
            current_extreme_values[0] = x
        elif x > current_extreme_values[2]:  # right. If its already the most left point, it can not be the most right aswell
            current_extreme_values[2] = x
        if y < current_extreme_values[1]:  # top
            current_extreme_values[1] = y
        elif y > current_extreme_values[3]:  # bot. If its already the most top point, it can not be the most bot aswell
            current_extreme_values[3] = y

        # if backtrack_value == -1, there is one more cluster and we add that
        # if points length == 0, no points left == last cluster found
        if (len(current_cluster) - backtrack_index) == -1 or len(points) == 0:
            # add new cluster
            clusters_points_list.append(current_cluster)
            extreme_values_list.append(current_extreme_values)
            if len(points) > 0: # reset values for new cluster
                current_cluster = []
                current_extreme_values = [current_point[0], current_point[1], current_point[0], current_point[1]]
                current_point = points[0]
                backtrack_index = 0
    return clusters_points_list, extreme_values_list


# creates a hull around a list of points
def create_hull(points, extreme_values, hulls, polygons):
    width = extreme_values[2] - extreme_values[0]
    height = extreme_values[3] - extreme_values[1]
    offset_x = extreme_values[0]
    offset_y = extreme_values[1]

    # create 2d array, where segment points are marked with a 1
    check_array = np.zeros((width + 1, height + 2))
    for point in points:
        check_array[point[0] - offset_x, point[1] - offset_y + 1] = 1

    hull_dict = {}

    # find corner points and save them in dictionary with the case as value
    for point in points:
        x = point[0] - offset_x
        y = point[1] - offset_y + 1

        # points around the current point
        top_left = 0 if x == 0 else check_array[x - 1, y - 1]
        top = check_array[x, y - 1]
        top_right = 0 if x == width else check_array[x + 1, y - 1]
        right = 0 if x == width else check_array[x + 1, y]
        bottom_right = 0 if (x == width or y == height + 1) else check_array[x + 1, y + 1]
        bottom = 0 if y == height + 1 else check_array[x, y + 1]
        bottom_left = 0 if (x == 0 or y == height + 1) else check_array[x - 1, y + 1]
        left = 0 if x == 0 else check_array[x - 1, y]

        # case 1 -> next point is right, 2 -> down, 3 -> left, 4 -> up
        # case 5 indicates, that searching for the next point will need the previous case,
        # because two corner points are overlapping

        # check regular corners.
        # corner is top left -> look for next point in right direction.
        if top == 0 and left == 0:
            if (x, y - 1) in hull_dict:
                hull_dict[(x, y - 1)] = 5
            else:
                hull_dict[(x, y - 1)] = 1
        # corner is top right -> look for next point in down direction.
        if top == 0 and right == 0:
            if (x + 1, y - 1) in hull_dict:
                hull_dict[(x + 1, y - 1)] = 5
            else:
                hull_dict[(x + 1, y - 1)] = 2
        # corner is bottom right -> look for next point in left direction.
        if bottom == 0 and right == 0:
            if (x + 1, y) in hull_dict:
                hull_dict[(x + 1, y)] = 5
            else:
                hull_dict[(x + 1, y)] = 3
        # corner is bottom left -> look for next point in up direction.
        if bottom == 0 and left == 0:
            if (x, y) in hull_dict:
                hull_dict[(x, y)] = 5
            else:
                hull_dict[(x, y)] = 4

        # check embedded corners.
        # corner is top left embedded  -> look for next point in up direction.
        if top == 1 and left == 1 and top_left == 0:
            hull_dict[(x, y - 1)] = 4
        # corner is top right embedded -> look for next point in right direction.
        if top == 1 and right == 1 and top_right == 0:
            hull_dict[(x + 1, y - 1)] = 1
        # corner is bottom right embedded -> look for next point in down direction.
        if bottom == 1 and right == 1 and bottom_right == 0:
            hull_dict[(x + 1, y)] = 2
        # corner is bottom left embedded -> look for next point in left direction.
        if bottom == 1 and left == 1 and bottom_left == 0:
            hull_dict[(x, y)] = 3

    # not needed, just for debugging
    corner_points_array = np.zeros((check_array.shape[0] + 1, check_array.shape[1]))
    for point in hull_dict.keys():
        corner_points_array[point[0], point[1]] = hull_dict[point]

    # find hull path clockwise and hulls counter clockwise
    hull_points = list(hull_dict.keys())
    polygon = []
    while hull_points:
        # first one in hull_points is always the most left and then top point of the hull.
        # That is important, to not start the path in a hole
        hull, hull_points = find_hulls_path(hull_points, hull_dict, offset_x, offset_y)
        hulls.append(hull)
        # if there is already at least one entry in polygon, it means the next hull found is a hole
        if polygon: # add hole to polygon
            # find the two points in hull and polygon, which are the closest
            curr_dist = extreme_values[2] + 1
            curr_polygon_point = (-1, -1)
            curr_hull_point = (-1, -1)
            curr_polygon_index = -1
            curr_hull_index = -1
            for p in range(len(polygon)):
                polygon_point = polygon[p]
                for h in range(len(hull)):
                    hull_point = hull[h]
                    points_dist = np.linalg.norm(np.mat(polygon_point) - np.mat(hull_point))
                    if points_dist < curr_dist:
                        curr_polygon_point = polygon_point
                        curr_hull_point = hull_point
                        curr_dist = points_dist
                        curr_polygon_index = p
                        curr_hull_index = h
            # rotate points in hull, so that curr_hull_point is the first element
            hull_rotated = hull[curr_hull_index:] + hull[:curr_hull_index]
            # shift the hole into the polygon
            hull_rotated = hull_rotated + [curr_hull_point, curr_polygon_point]
            polygon = polygon[:curr_polygon_index + 1] + hull_rotated + polygon[curr_polygon_index + 1:]
        else: # if there is nothing in polygon, it is the first hull and can just be added
            polygon = hull.copy()
    polygons.append(polygon)
    return hulls, polygons


# finds the path of the hull
def find_hulls_path(hull_points, hull_dict, offset_x, offset_y):
    # find hull path clockwise, and treat extended points accordingly
    hull_path = []
    # first one in hull_points is always the most left and then top point of the hull.
    current_point = hull_points[0]
    hull_points.remove(current_point)
    hull_path.append([current_point[0] + offset_x, current_point[1] + offset_y])

    current_case = hull_dict[current_point]  # 1 = go right, 2 = go down, 3 = go left, 4 = go up
    # if there is no next point found, the loop ends and the hull has been found
    while current_point != (-1, -1):
        x = current_point[0]
        y = current_point[1]

        # if current_case > 4, it means that current_point is a corner point two times
        # and the next case is dependent on the previous one
        if current_case == 1: # search for next point right
            current_point = check_right(x, y, hull_points)
            current_case = hull_dict[current_point] if current_point in hull_dict else -1
            if current_case > 4:
                current_case = 2
        elif current_case == 2: # search for next point down
            current_point = check_down(x, y, hull_points)
            current_case = hull_dict[current_point] if current_point in hull_dict else -1
            if current_case > 4:
                current_case = 3
        elif current_case == 3: # search for next point left
            current_point = check_left(x, y, hull_points)
            current_case = hull_dict[current_point] if current_point in hull_dict else -1
            if current_case > 4:
                current_case = 4
        elif current_case == 4: # search for next point up
            current_point = check_up(x, y, hull_points)
            current_case = hull_dict[current_point] if current_point in hull_dict else -1
            if current_case > 4:
                current_case = 1

        if current_point in hull_points:
            # if case = 5, it means that current_point is still a corner point once more, so it can not be deleted
            if hull_dict[current_point] == 5:
                # mark with a 6, so the second time it is the current point, it gets deleted
                hull_dict[current_point] = 6
            else:
                hull_points.remove(current_point) # dont delete all if hull_dict[current_point] == 9
            hull_path.append([current_point[0] + offset_x, current_point[1] + offset_y])

    return hull_path, hull_points


# checks if there is a point in a given list of points in the up direction and returns it if there is
def check_up(x, y, hull_points):
    current_dist = -1
    current_point = (-1, -1)
    for point in hull_points:
        if x == point[0] and y > point[1] and (y - point[1] < current_dist or current_dist == -1):
            current_point = point
            current_dist = y - point[1]
    return current_point


# checks if there is a point in a given list of points in the right direction and returns it if there is
def check_right(x, y, hull_points):
    current_dist = -1
    current_point = (-1, -1)
    for point in hull_points:
        if y == point[1] and x < point[0] and (point[0] - x < current_dist or current_dist == -1):
            current_point = point
            current_dist = point[0] - x
    return current_point


# checks if there is a point in a given list of points in the down direction and returns it if there is
def check_down(x, y, hull_points):
    current_dist = -1
    current_point = (-1, -1)
    for point in hull_points:
        if x == point[0] and y < point[1] and (point[1] - y < current_dist or current_dist == -1):
            current_point = point
            current_dist = point[1] - y
    return current_point


# checks if there is a point in a given list of points in the left direction and returns it if there is
def check_left(x, y, hull_points):
    current_dist = -1
    current_point = (-1, -1)
    for point in hull_points:
        if y == point[1] and x > point[0] and (x - point[0] < current_dist or current_dist == -1):
            current_point = point
            current_dist = x - point[0]
    return current_point


# -------------------------
#         Skript
# -------------------------

logging.basicConfig(filename='../tmp/full.log', level=logging.DEBUG)

print("Start " + u.colored_string("add hulls", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Start add hulls at: " + time.strftime("%H:%M:%S", time.localtime()))

for ensembleIndex in range(len(ai.ENSEMBLE_INFOS)):
    # load data
    start_load = time.time()
    segments = s.load(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat')

    print("Done " + u.colored_string("loading", "blue") + " " + str(len(segments)) + " segments for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_load))
    logging.debug("Done loading " + str(len(segments)) + " segments for field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_load))

    # adding hulls
    start_calc = time.time()

    for seg in segments:
        segments[seg].hulls, segments[seg].polygons = calculate_hull(segments[seg].get_pixel(segments))

    print("Done calculating " + u.colored_string("hulls", "blue") + " for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_calc))
    logging.debug("Done calculating hulls for field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_calc))

    # saving result in segments
    start_save = time.time()
    s.save(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat', segments)

    print("Done " + u.colored_string("saving", "blue") + " field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_save))
    logging.debug("Done saving field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_save))

print("Finished " + u.colored_string("add hulls", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
