import argparse
import base64
from io import BytesIO
import matplotlib
import time as t
matplotlib.use('Agg')

import api_helper as ah
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

from utils import mds_image

import artificial_info as ai


class Cachable:
    cache = {}

    def find_or_calculate(self, key, logic, arguments):
        if key in self.cache:
            return self.cache[key]
        self.cache[key] = logic(*arguments)

        return self.cache[key]
        # pass


# Artificial
class Global(Cachable):
   segments = {} # Do not change
   linkage_method = 'centroid' # Do not change (can be adapted interactively in the GUI)
   tree = None # Do not change
   altitudes = [] # Do not change
   name = ""
   id = 0
   tree_height = 0
   max_watershed_level = 100


app = Flask(__name__)
CORS(app)

g = []

current_gx = 0
current_gy = 0


def error(message):
    return jsonify({
        "status": 419,
        "data": message
    })


def json(data):
    return jsonify(data)


@app.route("/get-number-of-fields")
def get_number_of_fields():
    return json(len(ai.ENSEMBLE_INFOS))


@app.route("/get-field-names")
def get_field_names():
    field_names = []
    for i in ai.ENSEMBLE_INFOS:
        field_names.append(i[2])
    return json(field_names)


@app.route("/get-tree-height/<axis>")
def get_tree_height(axis):
    axis = int(axis)
    if axis == 0:
        response = g[current_gx].tree_height
    else:
        response = g[current_gy].tree_height
    return json(response)


@app.route("/get-max-watershed-level/<axis>")
def get_max_watershed_level(axis):
    axis = int(axis)
    if axis == 0:
        response = g[current_gx].max_watershed_level
    else:
        response = g[current_gy].max_watershed_level
    return json(response)


@app.route("/get-mds-image/<field>/<swap>", methods=['GET'])
def get_mds_image(field, swap=False):
    start_time = t.time()
    field_index = 0
    for i in range(len(ai.ENSEMBLE_INFOS)):
        if ai.ENSEMBLE_INFOS[i][2] == field:
            field_index = i

    mds_points = mds_image(np.load(ai.MDS_PATH + "y_full_" + str(field_index) + ".npy"), [ai.SHAPE[1], ai.SHAPE[2]])
    b = BytesIO()
    mds_img = (mds_points * 255).astype(np.uint8)

    if swap == 'true':
        print('swapping')
        mds_img = np.hstack([mds_img[:, mds_img.shape[1] // 2:], mds_img[:, :mds_img.shape[1] // 2]])

    im = Image.fromarray(mds_img)
    im.save(b, format='PNG')

    binary_fc = open(ai.COASTLINE, 'rb').read()
    overlay = base64.b64encode(binary_fc).decode('utf-8')
    result = {
        "image": base64.b64encode(b.getvalue()).decode("utf-8"),
        "overlay": overlay
    }
    print('... calculated mds image in %s seconds' % (t.time() - start_time))
    return json(result)


@app.route("/get-time-lag-range", methods=['GET'])
def get_time_lag_range():
    time_lag_range = [- ai.MAX_TIME_LAG, ai.MAX_TIME_LAG]
    return json(time_lag_range)


@app.route("/get-thresholds", methods=['GET'])
def get_thresholds():
    return json(ai.THRESHOLDS)


@app.route("/get-segments-by-watershed-level/<axis>/<watershed_level>/<name>", methods=['GET'])
def get_segments_by_watershed_level(axis, watershed_level, name):
    if name is None:
        name = ai.ENSEMBLE_INFOS[0][2]
    axis = int(axis)
    start_time = t.time()
    global current_gx
    global current_gy
    watershed_level = int(watershed_level)
    if axis == 0:
        current_gx = ah.get_index_by_name(name)
        name = g[current_gx].name
        segments = g[current_gx].find_or_calculate(f'segments-{current_gx}-ws-{watershed_level}',
                                                   ah.get_segment_list, (g[current_gx], watershed_level))
    else:
        current_gy = ah.get_index_by_name(name)
        name = g[current_gy].name
        segments = g[current_gy].find_or_calculate(f'segments-{current_gy}-ws-{watershed_level}',
                                                   ah.get_segment_list, (g[current_gy], watershed_level))
    result = {
        "dimensions": [ai.SHAPE[1], ai.SHAPE[2]],
        "watershed_level": watershed_level,
        "segments": segments,
        "name": name
    }
    print('... calculated segments in %s seconds' % (t.time() - start_time))
    return json(result)


@app.route("/refine-segment/<axis>/<segments>/<watershed_level>", methods=['GET'])
def refine_segment(axis, segments, watershed_level):
    start_time = t.time()
    watershed_level = int(watershed_level)
    segments = list(map(int, segments.split(',')))
    axis = int(axis)
    if axis == 0:
        segments_out = ah.get_segment_list(g[current_gx], watershed_level, segments)
    else:
        segments_out = ah.get_segment_list(g[current_gy], watershed_level, segments)
    result = {
        "axis": axis,
        "watershed_level": watershed_level,
        "segments": segments_out
    }
    print('... calculated refinement for segments in %s seconds' % (t.time() - start_time))
    return json(result)


@app.route("/get-curves-for-segments/<axis>/<segments>", methods=['GET'])
def get_curves_for_segments(axis, segments):
    axis = int(axis)
    start_time = t.time()
    curves = []
    segments = list(map(int, segments.split(',')))
    if axis == 0:
        current_g = current_gx
        for s in segments:
            curves.append(ah.get_curves_for_segment(g[current_gx], s))
    else:
        current_g = current_gy
        for s in segments:
            curves.append(ah.get_curves_for_segment(g[current_gy], s))
    result = {
        current_g: {
            s['segment']: s for s in curves
        }
    }
    print('... calculated curves for segments in %s seconds' % (t.time() - start_time))
    return json(result)


@app.route("/get-correlation-matrix-by-watershed-level/<watershed_level_x>/<watershed_level_y>/<threshold>/<linkage>", methods=['GET'])
@app.route("/get-correlation-matrix-by-watershed-level/<watershed_level_x>/<watershed_level_y>/<threshold>/<linkage>/<segments_x>/<segments_y>", methods=['GET'])
def get_correlation_matrix_by_watershed_level(watershed_level_x, watershed_level_y, threshold=None, linkage='single', segments_x=None, segments_y=None):
    start_time = t.time()
    watershed_level_x = int(watershed_level_x)
    watershed_level_y = int(watershed_level_y)

    if threshold is None:
        threshold = 0.9

    threshold = float(threshold)

    g[current_gx].linkage_method = linkage
    g[current_gy].linkage_method = linkage
    matrix, time_lags, row, col = ah.get_correlation_matrix(g[current_gx], g[current_gy], watershed_level_x, watershed_level_y,
                                                            segments_x, segments_y, threshold)
    color_dict_x = ah.get_color_dict(g[current_gx], row)
    color_dict_y = ah.get_color_dict(g[current_gy], col)

    row_length = len(row)
    col_length = len(col)
    result = {
        "dimensions": [row_length, col_length],
        "linkage": linkage,
        "threshold": threshold,
        "matrix": {
            "row_segments": row,
            "col_segments": col,
            "corrs": matrix,
            "time_lags": time_lags,
            "row_colors": color_dict_x,
            "col_colors": color_dict_y
        }
    }
    print('... calculated matrix in %s seconds' % (t.time() - start_time))
    return json(result)


@app.route("/hello-world", methods=['GET', 'POST'])
def hello_world():
    if request.method == 'GET':
        return 'Hi, i am the response to a GET request'
    if request.method == 'POST':
        return 'Hi, i am the response to a POST request'


if __name__ == '__main__':

    for i in range(len(ai.ENSEMBLE_INFOS)):
        g.append(Global())

    ah.setup(g)
    watershed_level = 20

    #get_correlation_matrix_by_watershed_level(100, 100, ai.THRESHOLDS[0], 'centroid')

    parser = argparse.ArgumentParser(description='Start the webserver.')
    parser.add_argument('--port', type=int, help='Port for the webserver (default 5000)', default=5000)
    parser.add_argument('--host', help='Host for the webserver (default 0.0.0.0)', default='0.0.0.0')
    args = vars(parser.parse_args())
    app.run(debug=False, port=args['port'], host=args['host'])

'''
    segments_x = get_segments_by_watershed_level(0, watershed_level, None)
    segments_y = get_segments_by_watershed_level(1, watershed_level, None)

    mds_image_x = get_mds_image(0)
    mds_image_y = get_mds_image(1)

    matrix = get_correlation_matrix_by_watershed_level(watershed_level, watershed_level, ai.THRESHOLDS[0], 'centroid')
    
    segments_x_keys = ""
    for segment in segments_x["segments"]:
        segments_x_keys += str(segment["segment"]) + ","
    segments_x_keys = segments_x_keys[:-1]

    segments_y_keys = ""
    for segment in segments_y["segments"]:
        segments_y_keys += str(segment["segment"]) + ","
    segments_y_keys = segments_y_keys[:-1]

    refined_segment_x = refine_segment(0, segments_x_keys, watershed_level)
    refined_segment_y = refine_segment(1, segments_y_keys, watershed_level)

    curve_segment_x = get_curves_for_segments(0, segments_x_keys)
    curve_segment_y = get_curves_for_segments(1, segments_y_keys)
    '''
