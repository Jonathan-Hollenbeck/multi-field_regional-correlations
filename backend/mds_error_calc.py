import numpy as np
import utils as u
import higra as hg
import matplotlib.pyplot as plt


ROOT_PATH = '../../world_normal_pr_ts_psl_09'
MDS_PATH = ROOT_PATH + '/mds/'
SHAPE = (1128, 96, 192)


def data_number_to_string(n):
    if n == 0:
        return "precipitation"
    elif n == 1:
        return "tempeture_surface"
    return "pressure_sea_level"


def threshold_number_to_string(t):
    if t == 0:
        return "1.0"
    elif t == 1:
        return "0.7"
    elif t == 2:
        return "0.5"
    elif t == 3:
        return "0.3"
    return "0.1"


base_data_paths = [
    MDS_PATH + 'y_full_precipitation_normal.npy',
    MDS_PATH + 'y_full_temperature_surface_normal.npy',
    MDS_PATH + 'y_full_pressure_sea_level_normal.npy'
]

compare_data_paths = [
    [
        MDS_PATH + 'y_full_precipitation_landmark+1.0.npy',
        MDS_PATH + 'y_full_precipitation_landmark+0.7.npy',
        MDS_PATH + 'y_full_precipitation_landmark+0.5.npy',
        MDS_PATH + 'y_full_precipitation_landmark+0.3.npy',
        MDS_PATH + 'y_full_precipitation_landmark+0.1.npy'
    ],
    [
        MDS_PATH + 'y_full_temperature_surface_landmark+1.0.npy',
        MDS_PATH + 'y_full_temperature_surface_landmark+0.7.npy',
        MDS_PATH + 'y_full_temperature_surface_landmark+0.5.npy',
        MDS_PATH + 'y_full_temperature_surface_landmark+0.3.npy',
        MDS_PATH + 'y_full_temperature_surface_landmark+0.1.npy'
    ],
    [
        MDS_PATH + 'y_full_pressure_sea_level_landmark+1.0.npy',
        MDS_PATH + 'y_full_pressure_sea_level_landmark+0.7.npy',
        MDS_PATH + 'y_full_pressure_sea_level_landmark+0.5.npy',
        MDS_PATH + 'y_full_pressure_sea_level_landmark+0.3.npy',
        MDS_PATH + 'y_full_pressure_sea_level_landmark+0.1.npy'
    ]
]


# Calculate hierarchical segmentation
def calculate_tree(mds_points):
    # MDS image in RGB space
    image_shape = SHAPE[1:]
    mds_points = u.normalize_point(mds_points)
    mds_image = np.reshape(mds_points, (*image_shape, mds_points.shape[-1]))
    size = mds_image.shape[:2]
    # graph
    tree, altitudes = u.create_graph(mds_image, size)

    return tree, altitudes


def prune_altitudes(altitudes):
    pruned_altitudes = set([])
    for altitude in altitudes:
        pruned_altitudes.add(altitude)

    return np.sort(np.array(list(pruned_altitudes)))


def calculate_altitude_to_segment_count(tree, altitudes):
    cut_helper = hg.HorizontalCutExplorer(tree, altitudes)
    altitudes = prune_altitudes(altitudes)
    alt_to_seg_count = []
    for i in range(int(altitudes[len(altitudes) - 1] + 1)):
        cut = cut_helper.horizontal_cut_from_altitude(i)
        nodes = cut.nodes()
        alt_to_seg_count.append(len(nodes))

    return np.array(alt_to_seg_count)


def calculate_tree_distance(tree_a, altitudes_a, tree_b, altitudes_b):
    distance = 0
    base_alt_to_seg = calculate_altitude_to_segment_count(tree_a, altitudes_a)
    compare_alt_to_seg = calculate_altitude_to_segment_count(tree_b, altitudes_b)

    length = len(base_alt_to_seg) if len(base_alt_to_seg) <= len(compare_alt_to_seg) else len(compare_alt_to_seg)
    distance += np.absolute(len(base_alt_to_seg) - len(compare_alt_to_seg))

    for i in range(length):
        diff = np.absolute(base_alt_to_seg[i] - compare_alt_to_seg[i])
        distance += 0 if diff == 0 else 1

    return distance


def calculate_mds_distance(mds_points_a, mds_points_b):
    absolute_difference = 0
    percentage_difference = 0

    for i in range(len(mds_points_a)):
        p_a = mds_points_a[i]
        p_b = mds_points_b[i]
        diff = abs(p_a - p_b)
        for k in range(len(p_a)):
            absolute_difference += diff[k]
            percentage_difference += (diff[k] / abs(p_a[k])) * 100

    points_amount = len(mds_points_a) * len(mds_points_a[0])

    absolute_difference /= points_amount
    percentage_difference /= points_amount

    return absolute_difference, percentage_difference


result_print = []

precipitation_values_abs = []
temperature_values_abs = []
pressure_values_abs = []
mean_values_abs = []

precipitation_values_prc = []
temperature_values_prc = []
pressure_values_prc = []
mean_values_prc = []

for d in range(len(base_data_paths)):
    mds_points_base = np.load(base_data_paths[d])
    base_graph, base_altitudes = calculate_tree(mds_points_base)
    print("\nloaded field: " + str(data_number_to_string(d)))

    result_print.append("\nfield: " + str(data_number_to_string(d)))
    control_distance = calculate_tree_distance(base_graph, base_altitudes, base_graph, base_altitudes)
    print("calculated distance for base field " + str(data_number_to_string(d)))
    control_percentage = (control_distance * 100) / base_altitudes[len(base_altitudes) - 1]
    result_print.append("base error: " + str(round(control_percentage, 2)) + "%")

    for t in range(len(compare_data_paths[d])):
        mds_points_compare = np.load(compare_data_paths[d][t])
        compare_graph, compare_altitudes = calculate_tree(mds_points_compare)
        print("loaded lmds+" + str(threshold_number_to_string(t)))

        #distance = calculate_tree_distance(base_graph, base_altitudes, compare_graph, compare_altitudes)
        #print("calculated distance for lmds+" + str(threshold_number_to_string(t)))
        #percentage = (distance * 100) / base_altitudes[len(base_altitudes) - 1]

        absolute_difference, percentage_difference = calculate_mds_distance(mds_points_base, mds_points_compare)

        #result_print.append("lmds+" + str(threshold_number_to_string(t)) + " error: " + str(round(percentage, 2)) + "%")
        result_print.append("lmds+" + str(threshold_number_to_string(t)) + " mds abs diff: " + str(round(absolute_difference, 10)))
        result_print.append("lmds+" + str(threshold_number_to_string(t)) + " mds perc diff: " + str(round(percentage_difference, 2)) + "%")

        if len(mean_values_abs) == t:
            mean_values_abs.append(absolute_difference / 3)
        else:
            mean_values_abs[t] += absolute_difference / 3

        if len(mean_values_prc) == t:
            mean_values_prc.append(percentage_difference / 3)
        else:
            mean_values_prc[t] += percentage_difference / 3

        if d == 0:
            precipitation_values_abs.append(absolute_difference)
            precipitation_values_prc.append(percentage_difference)
        elif d == 1:
            temperature_values_abs.append(absolute_difference)
            temperature_values_prc.append(percentage_difference)
        else:
            pressure_values_abs.append(absolute_difference)
            pressure_values_prc.append(percentage_difference)


for result in result_print:
    print(result)


# plot line graphs
landmark_points = [1.0, 0.7, 0.5, 0.3, 0.1]

figure, axis = plt.subplots()

#absolute
axis.plot(landmark_points, precipitation_values_abs)
axis.plot(landmark_points, temperature_values_abs)
axis.plot(landmark_points, pressure_values_abs)
axis.plot(landmark_points, mean_values_abs)
axis.set_xlabel("landmark size")
axis.set_ylabel("error")

#time

precipitation_values_time = [15056, 5176, 2008, 437, 18]
temperature_values_time = [14678, 5157, 2058, 429, 17]
pressure_values_time = [13676, 5280, 1981, 423, 17]
mean_values_time = [14470, 5204, 2016, 430, 17]

axis1 = axis.twinx()
axis1.plot(landmark_points, precipitation_values_time, label="precipitation")
axis1.plot(landmark_points, temperature_values_time, label="temperature surface")
axis1.plot(landmark_points, pressure_values_time, label="pressure sea level")
axis1.plot(landmark_points, mean_values_time, label="mean")
axis1.set_ylabel("time in s")
axis1.legend(loc="upper center")

figure.suptitle("landmark error and time values")

plt.show()