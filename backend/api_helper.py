import segment as s
import higra as hg
import utils as u
import scipy.cluster.hierarchy as sch
import scipy.special._basic as schb
import numpy as np
import artificial_info as ai


# Load data and calculate herarchical segmentation
def setup(g):
    # Load data
    for i in range(len(ai.ENSEMBLE_INFOS)):
        calculate_tree(g[i], i)
        g[i].name = ai.ENSEMBLE_INFOS[i][2]
        g[i].id = i
        g[i].segments = s.load(ai.SEGMENTS_PATH + "segments_" + str(i) + ".dat")
        g[i].max_watershed_level = g[i].altitudes[g[i].altitudes.size - 2]
        g[i].tree_height = get_height(g[i].segments, g[i].tree.root(), 0)
    pass


# return the index of the given field name in the ensemble infos
def get_index_by_name(name):
    for i in range(len(ai.ENSEMBLE_INFOS)):
        if ai.ENSEMBLE_INFOS[i][2] == name:
            return i
    return 0


# Calculate hierarchical segmentation
def calculate_tree(g, field_index):
    # MDS image in RGB space
    mds_image = create_mds_img(field_index)
    size = mds_image.shape[:2]
    # graph
    g.tree, g.altitudes = u.create_graph(mds_image, size)


# Load mds data and create image in RGB space
def create_mds_img(field_index):
    mds_points = np.load(ai.MDS_PATH + "y_full_" + str(field_index) + ".npy")
    image_shape = ai.SHAPE[1:]
    mds_points = u.normalize_point(mds_points)
    mds_image = np.reshape(mds_points, (*image_shape, mds_points.shape[-1]))
    return mds_image


# Determine list of dictionaries for given watershed level
# with segment, hull, color, refinement_level as keys
def get_segment_list(g, watershed_level, segments=None):
    refinement_level = None
    if segments is None:
        nodes = get_list_of_nodes(g, watershed_level)
    else:
        refinement_level = watershed_level
        nodes = get_refined_nodes(g, segments, watershed_level)
    # fill list
    seg_list = []
    for n in nodes:
        seg_list.append({
            "segment": int(n),
            "hull": g.segments[n].hulls,
            "polygon": g.segments[n].polygons,
            "color": g.segments[n].get_color(),
            "refinement_level": refinement_level,
            "min": "%.2f" % g.segments[n].min,
            "max": "%.2f" % g.segments[n].max
        })
    return seg_list


# List of nodes in level
def get_list_of_nodes(g, watershed_level):
    cut_helper = hg.HorizontalCutExplorer(g.tree, g.altitudes)
    cut = cut_helper.horizontal_cut_from_altitude(watershed_level)
    nodes = cut.nodes()
    return nodes


# Return a list of nodes for a local refinement
# The function expects the segments to be refined
# and the watershed level to which the nodes should be refined
def get_refined_nodes(g, segments, watershed_level):
    # Definition from Higra-Documentation:
    # Two leaves are in the same region (ie. have the same label) if the altitude of their lowest common ancestor is strictly greater than the specified threshold.
    nodes = []
    for s in segments:
        if g.altitudes[s] <= watershed_level:
            print("No refinement")
            nodes = nodes + [s]
        else:
            nodes = nodes + get_children_below_level(g, s, watershed_level)
    return nodes


# Ordered correlation matrix for the given watershed level and thresholds
# The matrix is calculated for the given segments or otherwise for all
# segments on the given watershed level
def get_correlation_matrix(gx, gy, watershed_level_x, watershed_level_y, segments_x, segments_y, threshold):
    if segments_x is None or segments_y is None:
        nodes_x = get_list_of_nodes(gx, watershed_level_x).tolist()
        nodes_y = get_list_of_nodes(gy, watershed_level_y).tolist()
    else:
        nodes_x = list(set(map(int, segments_x.split(','))))
        nodes_y = list(set(map(int, segments_y.split(','))))

    corrs = np.empty((len(nodes_x), len(nodes_y)))
    time_lags = np.empty((len(nodes_x), len(nodes_y)))
    for x in range(len(nodes_x)):
        for y in range(len(nodes_y)):
            seg = gx.segments[nodes_x[x]]
            corr, time_lag = seg.get_correlation_time_lag_multi_field(nodes_y[y], gy.id, threshold)
            corrs[x, y] = round(corr, 2)
            time_lags[x, y] = round(time_lag, 2)

    print("Corr Matrix dims:" + str(corrs.shape))
    if corrs.shape[0] == 1 or corrs.shape[1] == 1:
        matrix = corrs.tolist()
        time_lags = time_lags.tolist()
        row = nodes_x
        column = nodes_y
    else:
        matrix, time_lags, row, column = sort_correlation_matrix(gx, gy, corrs, time_lags, nodes_x, nodes_y)
    return matrix, time_lags, row, column


# Sort the given correlation matrix as well as the timelags and
# nodes array by using a hierarchical clustering
def sort_correlation_matrix(gx, gy, corr, time_lags, nodes_x, nodes_y):
    Y = sch.linkage(corr, method=gx.linkage_method)
    Z1 = sch.dendrogram(Y)
    idx1 = Z1['leaves']
    Y2 = sch.linkage(corr.transpose(), method=gy.linkage_method)
    Z2 = sch.dendrogram(Y2)
    idy1 = Z2['leaves']
    corr = corr[idx1, :]
    corr = corr[:, idy1]
    time_lags = time_lags[idx1, :]
    time_lags = time_lags[:, idy1]
    nodes_x = np.array(nodes_x)
    nodes_y = np.array(nodes_y)
    row = nodes_x[idx1]
    col = nodes_y[idy1]
    return corr.tolist(), time_lags.tolist(), row.tolist(), col.tolist()


# Creates a dictionary that maps each segment to a color
def get_color_dict(g, row):
    dict = {}
    for s in row:
        dict[int(s)] = g.segments[s].get_color()
    return dict


# Returns the children of the given segment on the chosen watershed level
def get_children_below_level(g, segment, watershed_level):
    if g.segments[segment].is_leaf:
        return [segment]
    nodes = []
    for c in g.segments[segment].children:
        if g.altitudes[c] <= watershed_level:
            nodes.append(c)
        else:
            nodes += get_children_below_level(g, c, watershed_level)
    return nodes


# Calculate the dictionary with the data for the in detail view
def get_curves_for_segment(g, s):
    median, lower, upper = get_functional_boxplot_variant(g, s)
    color = g.segments[s].get_color()
    return {
        "segment": s,
        "median": median.tolist(),
        "lower_bound": lower,
        "lower_quartile": lower,
        "upper_quartile": upper,
        "upper_bound": upper,
        "outliers": None,
        "color": color,
        "width": (np.array(upper) - np.array(lower)).tolist()
    }


# Determines median curve and the curves that encapsulate the whole data
def get_functional_boxplot_variant(g, s):
    series = np.array(g.segments[s].means)
    lower = np.array(series).min(axis=0).tolist()
    upper = np.array(series).max(axis=0).tolist()
    # calculate median
    depth = banddepth(np.asarray(series))
    ix_depth = np.argsort(depth)[::-1]
    median = series[ix_depth[0], :]
    return median, lower, upper


def banddepth(data):
    n, p = data.shape
    rv = np.argsort(data, axis=0)
    rmat = np.argsort(rv, axis=0) + 1
    down = rmat - 1
    up = n - rmat

    return ((np.sum(up * down, axis=1) / p) + n - 1) / schb.comb(n, 2)


# Height for node in dendrogram tree
def get_height(segs, node, height):
    m = height
    if not segs[node].is_leaf:
        for c in segs[node].children:
            m = max(m, get_height(segs, c, height))
    return m + 1