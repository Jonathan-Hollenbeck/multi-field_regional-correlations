import numpy as np
import segment as s
import time
import data_manager
import artificial_info as ai
import utils as u

import logging

# -------------------------
#        Functions
# -------------------------


def get_timeline_indices(seg):
    # Return indices of timelines
    pixels = np.array(segments[seg].get_pixel(segments))
    # I have no idea why it is this way around but otherwise the results makes no sense
    indices = pixels[:, 1] * ai.SHAPE[2] + pixels[:, 0]
    return indices


# prints progress
def print_progress(iteration, max_iteration, start_time, length):
    percentage_done = 100 * iteration / max_iteration
    time_since_start = time.time() - start_time
    time_estimate = (100 / percentage_done) * time_since_start
    filledLength = int(length * iteration // max_iteration)
    bar = '█' * filledLength + '-' * (length - filledLength)
    print("\r" + str(round(percentage_done, 2)) + "% " + str(iteration) + "/" + str(max_iteration) +
          " " + u.colored_string(bar, "green") + " time since start: " +
          u.convert_seconds_to_string(time_since_start), end="")


# -------------------------
#         Skript
# -------------------------

logging.basicConfig(filename='../tmp/full.log', level=logging.DEBUG)

print("Start " + u.colored_string("add minmax", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Start add minmax at: " + time.strftime("%H:%M:%S", time.localtime()))

for ensembleIndex in range(len(ai.ENSEMBLE_INFOS)):
    # load Data
    start_load = time.time()

    data = data_manager.load_ensemble(ai.ENSEMBLE_INFOS[ensembleIndex], ai.subsample)

    print("Done " + u.colored_string("loading", "blue") + " data in: " + u.convert_seconds_to_string(time.time() - start_load))
    logging.debug("Done loading data in: " + u.convert_seconds_to_string(time.time() - start_load))

    # concatenate timelines
    start_conc = time.time()
    data_conc = u.concatenate_timelines(data)

    print("Done " + u.colored_string("concatenating", "blue") + " data of field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_conc))
    logging.debug("Done concatenating data of field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_conc))

    # load segments
    start_segs = time.time()
    segments = s.load(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat')

    print("Done " + u.colored_string("loading", "blue") + " " + str(len(segments)) + " segments of field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_segs))
    logging.debug("Done loading " + str(len(segments)) + " segments of field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_segs))

    # add minmax
    start_minmax = time.time()
    counter = 0
    for seg in segments:
        counter += 1
        times_seg_idx = get_timeline_indices(seg)
        corrs = np.corrcoef(data_conc[times_seg_idx])
        corrs = corrs - np.identity(corrs.shape[0]) * (1 - corrs[0, 1])
        segments[seg].min = np.min(corrs)
        segments[seg].max = np.max(corrs)
        print_progress(counter, len(segments), start_minmax, 50)

    print("\nDone adding " + u.colored_string("minmax", "blue") + " for field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_minmax))
    logging.debug("Done adding minmax for field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_minmax))

    start_save = time.time()
    s.save(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat', segments)

    print("Done " + u.colored_string("saving", "blue") + " field: " + u.colored_string(ai.ENSEMBLE_INFOS[ensembleIndex][2], "purple") + " in: " + u.convert_seconds_to_string(time.time() - start_save))
    logging.debug("Done saving field: " + ai.ENSEMBLE_INFOS[ensembleIndex][2] + " in: " + u.convert_seconds_to_string(time.time() - start_save))

print("Finished " + u.colored_string("add minmax", "blue") + " at: " + time.strftime("%H:%M:%S", time.localtime()))
logging.debug("Finished add minmax at: " + time.strftime("%H:%M:%S", time.localtime()))
