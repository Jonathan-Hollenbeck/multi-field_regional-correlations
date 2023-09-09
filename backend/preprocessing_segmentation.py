import numpy as np
import utils as u
import time
from joblib import Parallel, delayed
import segment
import data_manager
import artificial_info as ai
import logging
import copy

# Global variables
node_counter = 0
inner_corr_time = 0

segments_list = []


# -------------------------
#        Functions
# -------------------------


# Store segments from tree
def add_segments(tree, altitudes, shape, segments, current_index, parent_index):
    children = tree.children(current_index)
    if altitudes[current_index] > 0:
        segments[int(current_index)] = segment.Segment(parent_index, children, shape)
        for child in children:
            add_segments(tree, altitudes, shape, segments, child, current_index)
    else:
        # Leaf
        segments[int(current_index)] = segment.Segment(parent_index, children, shape, True)


# CORRELATIONS


# Add correlations to tree structure
def add_correlations(node, segments_base, segments_compare, compare_root, base_field_index, compare_field_index):
    # Basic idea: Calculate correlations among the segments under consideration and all segments in the branches determined
    # by the root nodes stored in branch_list
    global node_counter
    global inner_corr_time
    node_counter = node_counter + 1
    if time.time() - inner_corr_time > 5:
        inner_corr_time = time.time()
        print_progress(node_counter, len(segments_base), start_corr, 50)

    store_correlations(node, segments_base, segments_compare, compare_root, base_field_index, compare_field_index)

    if not segments_base[node].is_leaf:
        if len(segments_base[node].children) > 1:
            for c in segments_base[node].children:
                add_correlations(c, segments_base, segments_compare, compare_root, base_field_index, compare_field_index)
        else:
            add_correlations(segments[node].children[0], segments_base, segments_compare, compare_root, base_field_index, compare_field_index)


# Calculate correlations if necessary and store in respective segment
def store_correlations(node, segments_base, segments_compare, compare_node, base_field_index, compare_field_index):
    # First element of list is the node itself. On this point only necessary
    # to allows easy access later on
    b_node = segments_base[node]
    c_node = segments_compare[compare_node]
    corrs, lag = get_correlation(b_node.means, c_node.means, b_node.msc, c_node.msc)
    for t in ai.THRESHOLDS:
        corr = check_threshold(corrs, lag, t)
        if corr != 0:
            segments_base[node].add_correlation_multi_field(compare_node, compare_field_index, corr, lag - ai.MAX_TIME_LAG, t)
            segments_compare[compare_node].add_correlation_multi_field(node, base_field_index, corr, lag - ai.MAX_TIME_LAG, t)
    if not segments_compare[compare_node].is_leaf:
        h = u.get_height(segments_compare, compare_node, 0)
        if len(segments_compare[compare_node].children) > 1 and h > 9:
            #print("... \033[94mstore correlation\033[00m parallel in node " + str(node) + " with " + str(len(segments_compare[compare_node].children)) + " children and height " + str(h))
            Parallel(n_jobs=-1, backend="threading")(delayed(store_correlations)(node, segments_base, segments_compare, c, base_field_index, compare_field_index) for c in segments_compare[compare_node].children)
            #JUST FOR DEBUGGING
            #for c in segments_compare[compare_node].children:
            #    store_correlations(node, segments_base, segments_compare, c, base_field_index, compare_field_index)
        else:
            for c in segments_compare[compare_node].children:
                store_correlations(node, segments_base, segments_compare, c, base_field_index, compare_field_index)


# Determine thresholds correlations between means_a and means_b
def get_correlation(means_a, means_b, a_msc, b_msc):
    corrs = calculate_shifted_correlations(means_a, means_b, a_msc, b_msc)
    max_corr_i = np.argmax(np.absolute(corrs), axis=0)
    counts = np.bincount(max_corr_i)
    lag = np.argmax(counts)
    return corrs, lag


# checks if the resulting correlations exceed the given threshold
# and transformes the ones that do to a 1 or -1 and returns that
def check_threshold(corrs, lag, t):
    max_corr = copy.copy(corrs[lag])
    max_corr[max_corr >= t] = 1
    max_corr[np.logical_and(max_corr < t, max_corr > -t)] = 0
    max_corr[max_corr <= -t] = -1
    if 1 in np.unique(max_corr) and -1 in np.unique(max_corr):
        print("Strong positive and negative correlations!")
        print(corrs.shape)
        print(max_corr.shape)
    corr = np.mean(max_corr)
    return corr


# Determine correlations with a given time lag
def calculate_shifted_correlations(means_a, means_b, a_msc, b_msc):
    a = normalize_means(means_a)
    b = normalize_means(means_b)

    corrs = np.array(
        [
            np.correlate(a[i], b[i], mode='full')[len(a[i]) - 1 - ai.MAX_TIME_LAG : len(a[i]) + ai.MAX_TIME_LAG] /
            (a_msc[i] * b_msc[i])
            for i in range(len(means_a))
        ]
    ).transpose(1, 0)

    if np.any(corrs < -1.00001) or np.any(corrs > 1.00001):
        print("Problem!")
        print(np.min(corrs))
        print(np.max(corrs))
        exit()
    return corrs


# normalize means for shifted correlation calculation
def normalize_means(means):
    x_sub = np.array([np.mean(means, axis=1)]).transpose((1, 0))
    return np.subtract(means, x_sub)


# prints progress
def print_progress(iteration, max_iteration, start_time, length):
    percentage_done = 100 * iteration / max_iteration
    time_since_start = time.time() - start_time
    time_estimate = (100 / percentage_done) * time_since_start
    time_left = round(time_estimate - time_since_start, 0)
    filledLength = int(length * iteration // max_iteration)
    bar = '█' * filledLength + '-' * (length - filledLength)
    print("\r" + str(round(percentage_done, 2)) + "% " + str(iteration) + "/" + str(max_iteration) +
          " " + u.colored_string(bar, "green") + " time since start: " +
          u.convert_seconds_to_string(time_since_start) + " full time: " + u.convert_seconds_to_string(
        time_estimate) + " time left: " + u.convert_seconds_to_string(time_left), end="")


# MEANS


# Calculate mean for the respective segment (node) and store the result in it
def add_means(node, segments, data):
    if segments[node].is_leaf:
        segments[node].means = get_ensemble_means(node, segments, data)
    else:
        means = []
        area_size = 0
        for c in segments[node].children:
            add_means(c, segments, data)
            num_pixel = len(segments[c].get_pixel(segments)[0])
            if len(means) == 0:
                means = num_pixel * segments[c].means
            else:
                means = means + num_pixel * segments[c].means
            area_size = area_size + num_pixel
        segments[node].means = means / area_size

    # precalculate standard deviation for performance in correlation calculation
    x = normalize_means(segments[node].means)
    segments[node].msc = np.array([np.sqrt(np.correlate(x[i], x[i]))
            for i in range(len(segments[node].means))])


# Determine ensemble means for segment seg
def get_ensemble_means(seg, segments, data):
    pixels = segments[seg].get_pixel(segments)
    ensemble_means = Parallel(n_jobs=-1, backend="threading")(delayed(calculate_segment_means)(pixels, data[i]) for i in range(len(data)))
    return np.array(ensemble_means)


# Calculate mean over given pixels
def calculate_segment_means(pixel, field):
    pixel = np.array(pixel)
    mean = np.mean(field[pixel[:,1], pixel[:,0]], axis=0)
    return mean


# -------------------------
#         Skript
# -------------------------

logging.basicConfig(filename='../tmp/full.log', level=logging.DEBUG)

print("Start " + u.colored_string("preprocessing segmentation", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Start preprocessing segmentation at: " + time.strftime("%H:%M:%S", time.localtime()))


# load data

for ensembleIndex in range(len(ai.ENSEMBLE_INFOS)):
    data = data_manager.load_ensemble(ai.ENSEMBLE_INFOS[ensembleIndex], ai.subsample)
    start = time.time()

    print("Start " + u.colored_string("segmentation", "blue") + " of field: \033[95m" + ai.ENSEMBLE_INFOS[ensembleIndex][2] + "\033[0m")
    logging.debug("Start segmentation of field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2])

    # Load mds data
    mds_points = np.load(ai.MDS_PATH + 'y_full_' + str(ensembleIndex) + '.npy')
    image_shape = ai.SHAPE[1:]
    mds_points = u.normalize_point(mds_points)
    mds_image = np.reshape(mds_points, (*image_shape, mds_points.shape[-1]))
    size = mds_image.shape[:2]

    # graph
    tree, altitudes = u.create_graph(mds_image, size)

    img_shape = (size[1], size[0])
    root_index = tree.root()

    #load segments; for debugging
    #segments = segment.load(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat')

    segments = {}
    add_segments(tree, altitudes, img_shape, segments, root_index, -1)

    print("Done with " + u.colored_string("segmenting", "blue") + " field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start))
    logging.debug("Done with segmenting field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start))

    print("Start " + u.colored_string("means", "blue") + " of field: \033[95m" + ai.ENSEMBLE_INFOS[ensembleIndex][2] + "\033[0m")
    logging.debug("Start means of field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2])

    start_means = time.time()

    # add means to segments
    add_means(root_index, segments, data)
    
    print("Done with " + u.colored_string("means", "blue") + " for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_means))
    logging.debug("Done with means for field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_means))

    # clear correlation dict in segments to prevent mistakes
    for s in segments:
        segments[s].correlations = {}

    # add segments to list for correlation later
    segments_list.append([segments, root_index])


# correlation
start_corr_full = time.time()
for base in range(len(ai.ENSEMBLE_INFOS)):
    for compare in range(len(ai.ENSEMBLE_INFOS) - base):
        start_corr = time.time()
        compare = compare + base
        print("Start " + u.colored_string("correlations", "blue") + " between fields: " + u.colored_string(ai.ENSEMBLE_INFOS[base][2], "purple") + " and " + u.colored_string(ai.ENSEMBLE_INFOS[compare][2], "purple") + " with Thresholds " + str(ai.THRESHOLDS))
        logging.debug("Start correlations between fields: " + ai.ENSEMBLE_INFOS[base][2] + " and " + ai.ENSEMBLE_INFOS[compare][2] + " with Thresholds " + str(ai.THRESHOLDS))

        # getting the segments of the fields to correlate
        segments_base = segments_list[base][0]
        segments_compare = segments_list[compare][0]

        # and the root indexes
        root_index_base = segments_list[base][1]
        root_index_compare = segments_list[compare][1]

        # calculate correlations between segments
        inner_corr_time = time.time()

        add_correlations(root_index_base, segments_base, segments_compare, root_index_compare, base, compare)
        print_progress(node_counter, len(segments_base), start_corr, 50)

        node_counter = 0

        print("\nDone with " + u.colored_string("correlations", "blue") + " between fields: " + u.colored_string(ai.ENSEMBLE_INFOS[base][2], "purple") + " and " + u.colored_string(ai.ENSEMBLE_INFOS[compare][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_corr))
        logging.debug("Done with correlations between fields: " + ai.ENSEMBLE_INFOS[base][2] + " and " + ai.ENSEMBLE_INFOS[compare][2] + " in: " + u.convert_seconds_to_string(time.time() - start_corr))

# save correlations in segments
for index in range(len(segments_list)):
    start_save = time.time()
    segment.save(ai.SEGMENTS_PATH + 'segments_' + str(index) + '.dat', segments_list[index][0])
    print("Done " + u.colored_string("saving", "blue") + " field: " + u.colored_string(ai.ENSEMBLE_INFOS[index][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_save))
    logging.debug("Done saving field: " + ai.ENSEMBLE_INFOS[index][2] + " in: " + u.convert_seconds_to_string(time.time() - start_save))

print("Finished " + u.colored_string("preprocessing segmentation", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Finished preprocessing segmentation at: " + time.strftime("%H:%M:%S", time.localtime()))
