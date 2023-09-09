import numpy as np
import logging
import time as time

import artificial_info as ai
import utils as u
import data_manager

from helper.mds import mds
from helper.landmark_mds import landmark_mds
from helper.pearson import pearson_corr_distance_matrix

# -------------------------
#         Skript
# -------------------------

logging.basicConfig(filename='../tmp/full.log', level=logging.DEBUG)

print("Start " + u.colored_string("multifield correlate multiple fields", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Start multifield correlate multiple fields at: " + time.strftime("%H:%M:%S", time.localtime()))

for ensembleIndex in range(len(ai.ENSEMBLE_INFOS)):
    # load Data
    print("Start " + u.colored_string("loading", "blue") + " data")
    logging.debug("Start loading data")
    start_time = time.time()

    data = data_manager.load_ensemble(ai.ENSEMBLE_INFOS[ensembleIndex], ai.subsample)

    print("Done with " + u.colored_string("loading", "blue") + " data in: " + u.convert_seconds_to_string(time.time() - start_time))
    logging.debug("Done with loading data in: " + u.convert_seconds_to_string(time.time() - start_time))

    # Distance matrices

    print("Start calculating " + u.colored_string("distance matrix", "blue"))
    logging.debug("Start calculating distance matrix")
    start_time = time.time()

    part_time = time.time()
    # load correlations; for debugging
    # distance_matrix = np.load(ai.CORR_PATH + 'corr_full_' + str(ensembleIndex) + '.npy')

    timelines = u.concatenate_timelines(data)
    print("... Done with " + u.colored_string("concatenating timelines", "blue") + " of field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.colored_string(u.convert_seconds_to_string(time.time() - part_time), "black"))
    logging.debug("... Done with concatenating timelines of field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - part_time))

    distance_matrix = pearson_corr_distance_matrix(timelines=timelines, lag=0)
    np.save(ai.CORR_PATH + 'corr_full_' + str(ensembleIndex) + '.npy', distance_matrix)
    print("... Done with " + u.colored_string("distance matrix", "blue") + " of field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.colored_string(u.convert_seconds_to_string(time.time() - part_time), "black"))
    logging.debug("... Done with distance matrix of field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - part_time))

    print("Done with calculating " + u.colored_string("distance matrix", "blue") + " in: " + u.convert_seconds_to_string(time.time() - start_time))
    logging.debug("Done with calculating mdistance matrix in: " + u.convert_seconds_to_string(time.time() - start_time))


    # MDS

    print("Start calculating " + u.colored_string("mds", "blue"))
    logging.debug("Start calculating mds")
    start_time = time.time()

    # normalize correlation matrix to form distance_matrix
    distance_matrix = (1 - distance_matrix) * 0.5
    part_time = time.time()

    if ai.MDS_VARIANT == "landmark":
        print("... calculating " + u.colored_string("landmark", "blue") + " mds with sample size " + str(ai.SAMPLESIZE) + " for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple"))
        logging.debug("... calculating landmark mds with sample size " + str(ai.SAMPLESIZE) + " for field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2])
        sample_size = int(distance_matrix.shape[0] * ai.SAMPLESIZE)
        Y, eigens = landmark_mds(distance_matrix, sample_size, 3)
        print("... Done with " + u.colored_string("landmark", "blue") + " mds for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - part_time))
        logging.debug("... Done with landmark mds for field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - part_time))
        np.save(ai.MDS_PATH + 'y_full_' + str(ai.ENSEMBLE_INFOS[ensembleIndex][2]) + "_" + str(ai.MDS_VARIANT) + "+" + str(ai.SAMPLESIZE) + '.npy', Y)
    else:
        print("... calculating " + u.colored_string("normal", "blue") + " mds for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple"))
        logging.debug("... calculating normal mds for field:" + ai.ENSEMBLE_INFOS[ensembleIndex][2])
        Y, eigens = mds(distance_matrix, dimensions=3)
        print("... Done with " + u.colored_string("normal", "blue") + " mds for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - part_time))
        logging.debug("... Done with normal mds for field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - part_time))

    np.save(ai.MDS_PATH + 'y_full_' + str(ensembleIndex) + '.npy', Y)
    np.save(ai.EIGENS_PATH + 'eigens_full_' + str(ensembleIndex) + '.npy', eigens)

    data_manager.save_mds_image(Y, ensembleIndex)
    data_manager.save_color_cloud_plot(Y, ensembleIndex)

    print("Done with " + u.colored_string("mds", "blue") + " in: " + u.convert_seconds_to_string(time.time() - start_time))
    logging.debug("Done with mds in: " + u.convert_seconds_to_string(time.time() - start_time))

print("Finished " + u.colored_string("multifield correlate multiple fields", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Finished multifield correlate multiple fields at: " + time.strftime("%H:%M:%S", time.localtime()))
