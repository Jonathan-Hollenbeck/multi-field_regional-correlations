import segment as s
import numpy as np
import utils as u
import time
import artificial_info as ai

import logging

# -------------------------
#        Functions
# -------------------------


# Calculate mean color for segment n
def get_mean_color(n, segments, mds_image):
    pixel = segments[n].get_pixel(segments)
    pixel = np.array(pixel)
    mean = (np.mean(mds_image[pixel[:, 1], pixel[:, 0]], axis=0) * 255).tolist()
    mean.append(255)
    return mean


# Convert maximum standard deviation to color
def get_max_std_color(std, max_std):
    v = (1.0-std/max_std) * 255
    return [v, v, v, 255]


# Get number of child segments for segment n
# converted to a color
def get_num_child_segments(n, segments, max):
    # Count children
    children = get_children(n, segments)
    v = (1.0-children/max) * 255
    return [v, v, v, 255]


# Determine number of leaves belonging to segment n
def get_children(n, segments):
    if(segments[n].is_leaf):
        return 1
    else:
        children = 0
        for c in segments[n].children:
            children = children + get_children(c, segments)
        return children

'''
# Determine the maximum standard deviation for segment seg
def get_max_std_dev(seg, segments):
    pixels, _ = segments[seg].get_pixel(segments)
    pixels = np.array(pixels)
    ensemble_runs = os.listdir(ENSEMBLE_PATH)
    time_series = None
    for e in ensemble_runs:
        ensemble_run_path = os.path.join(ENSEMBLE_PATH, e)
        f = netCDF4.Dataset(os.path.join(ensemble_run_path, os.listdir(ensemble_run_path)[0]))
        field = f.variables[FIELD_VARIABLE]
        field = np.transpose(field, (1, 2, 0))
        if(np.any(time_series == None)):
            time_series = field[pixels[:,1], pixels[:,0]]
        else:
            time_series = time_series + field[pixels[:,1], pixels[:,0]]
    time_series = time_series/len(ensemble_runs)
    std = np.std(time_series, axis = 0)
    max = np.max(std)
    return max
'''


# Determine minimum correlation with segment seg involved, converted to color
def get_min_corr(seg, segments, threshold):
    v = 0
    # Get nodes
    if(segments[seg].is_leaf):
        return [v, v, v, 255]
    nodes = get_leaf_nodes(seg, segments)
    # Get matrix
    matrix = get_correlation_matrix_from_nodes(nodes, segments, threshold)
    min = np.min(matrix)
    # Create color from min
    v = (1.0-0.5*(min+1))*255
    return [v, v, v, 255]


# Determine leaves belonging to segment n
def get_leaf_nodes(seg, segments):
    nodes = []
    if(segments[seg].is_leaf):
        nodes = [seg]
    else:
        for c in segments[seg].children:
            nodes = nodes + get_leaf_nodes(c, segments)
    return nodes


# Determine correlation matrix for a list of segments
def get_correlation_matrix_from_nodes(nodes, segments, threshold):
    corr = np.empty((len(nodes), len(nodes)))
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if(i==j):
                corr[i,j]=1
            else:
                if(str(threshold) in segments[nodes[i]].correlations and nodes[j] in segments[nodes[i]].correlations[str(threshold)]):
                    corr[i,j]=segments[nodes[i]].correlations[str(threshold)][nodes[j]][0]
                else:
                    print("Ups, Problem")
                    exit()
    return corr


# -------------------------
#         Skript
# -------------------------

logging.basicConfig(filename='../tmp/full.log', level=logging.DEBUG)

print("Start " + u.colored_string("add color", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Start add color at: " + time.strftime("%H:%M:%S", time.localtime()))

for ensembleIndex in range(len(ai.ENSEMBLE_INFOS)):
    # load data
    start_load = time.time()
    segments = s.load(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat')

    print("Done " + u.colored_string("loading", "blue") + " " + str(len(segments)) + " segments of field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_load))
    logging.debug("Done loading " + str(len(segments)) + " segments of field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_load))

    # load mds points
    start_calc = time.time()
    mds_points = np.load(ai.MDS_PATH + 'y_full_' + str(ensembleIndex) + '.npy')
    image_shape = ai.SHAPE[1:]
    mds_image_lab = u.mds_image(mds_points, image_shape)

    # Number of segments
    num_segs = 0
    for seg in segments:
        if(segments[seg].is_leaf):
            num_segs = num_segs + 1

    # adding color
    for seg in segments:
        segments[seg].colors = {}
        segments[seg].colors["mean_lab"] = get_mean_color(seg, segments, mds_image_lab)

    print("Done adding " + u.colored_string("colors", "blue") + " for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_calc))
    logging.debug("Done adding colors for field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_calc))


    start_save = time.time()
    s.save(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat', segments)

    print("Done " + u.colored_string("saving", "blue") + " field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_save))
    logging.debug("Done saving field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_save))

print("Finished " + u.colored_string("add color", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Finished add color at: " + time.strftime("%H:%M:%S", time.localtime()))
