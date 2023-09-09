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

    # save result in segments
    start_save = time.time()
    s.save(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat', segments)

    print("Done " + u.colored_string("saving", "blue") + " field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_save))
    logging.debug("Done saving field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_save))

print("Finished " + u.colored_string("add color", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Finished add color at: " + time.strftime("%H:%M:%S", time.localtime()))
