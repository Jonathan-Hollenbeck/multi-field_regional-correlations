import alphashape
import numpy as np
import artificial_info as ai
import segment as s


def calculate_hull(segments, n):
    segment_points = segments[n].get_pixel(segments)
    is_split, split_idx = test_split_segment(segment_points)
    # Here only split in x-direction
    hull = alphashape.alphashape(segment_points, 1)
    try:
        hull = np.array([hull.exterior.coords.xy[1], hull.exterior.coords.xy[0]]).T.tolist()
    except Exception as e:
        if len(hull) > 0:
            hulls = []
            for h in hull:
                hulls.append(np.array([h.exterior.coords.xy[1], h.exterior.coords.xy[0]]).T.tolist())
            return hulls, hulls
        else:
            return [[[]]], [[[]]]
    if is_split:
        hull = split_points(segment_points, split_idx)
        return hull, hull
    else:
        hull = segment_points
    return [hull], [hull]


def test_split_segment(points):
    points = np.array(points)
    # x-direction
    x_diff = np.diff(np.unique(points[:,0]))
    if(np.any(x_diff > 1)):
        return True, int(np.arange(len(x_diff))[x_diff>1])
    # y-direction not relevant for our dataset
    return False, 0


def split_points(segment_points, idx):
    # Split only in x-direction possible (choice of datasets)
    points = np.array(segment_points)
    first = points[points[:,0]<=idx].tolist()
    second = points[points[:,0]>idx].tolist()
    return [first, second]


for ensembleIndex in range(len(ai.ENSEMBLE_INFOS)):
    # load data
    segments = s.load(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat')

    for seg in segments:
        segments[seg].polygons, segments[seg].polygons = calculate_hull(segments, seg)
    s.save(ai.SEGMENTS_PATH + 'segments_' + str(ensembleIndex) + '.dat', segments)
    print("finished")
