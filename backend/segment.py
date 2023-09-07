import numpy as np
import json
import zlib


class Segment(object):
    is_leaf = False
    children = [] # For leaf: children = pixel!
    parent = 0 # Root: parent = -1
    correlations = {} # Dictionary with str(threshold) as key, value: dictionary with index as key, pair (corr, lag) as value
    shape = None
    means = None
    colors = {}
    hulls = None
    polygons = None
    min = 0
    max = 0
    msc = None

    def __init__(self, parent, children, shape, is_leaf=False):
        self.parent = parent
        self.children = list(children)
        self.shape = shape
        self.is_leaf = is_leaf

    # Return list of pixels (as 2D array) and if it is a line
    def get_pixel(self, segments_list):
        pixel_2d = []
        if self.is_leaf:
            pixel = self.children
            # Reshape pixel
            for p in pixel:
                x, y = self.reshape_pixel(p)
                pixel_2d.append([x, y])
        else:
            for child in self.children:
                children_pixels = segments_list[child].get_pixel(segments_list)
                pixel_2d = pixel_2d + children_pixels
        return pixel_2d

    # Creates cartesian coordinates for a list of values
    def reshape_pixel(self, p):
        x = int(p % self.shape[0])
        y = int(p / self.shape[0])
        return x, y

    def add_correlation(self, segment_index, corr, lag, threshold):
        if not str(threshold) in self.correlations:
            self.correlations[str(threshold)] = {}
        self.correlations[str(threshold)][int(segment_index)] = (float(corr), int(lag))

    def add_correlation_multi_field(self, segment_index, field_index, corr, lag, threshold):
        if not str(threshold) in self.correlations:
            self.correlations[str(threshold)] = {}
        if not int(field_index) in self.correlations[str(threshold)]:
            self.correlations[str(threshold)][int(field_index)] = {}
        self.correlations[str(threshold)][int(field_index)][int(segment_index)] = (float(corr), int(lag))

    def get_color(self, type_="mean_lab"):
        color = np.random.rand(4)*255
        if np.all(self.colors is None):
            return color.tolist()
        if type_ in self.colors:
            color = self.colors[type_]
        if not isinstance(color, list):
            color = color.tolist()
        return color

    def get_correlation(self, index, threshold):
        corr = self.correlations[str(threshold)][index][0]
        return corr

    def get_correlation_time_lag_multi_field(self, segment_index, field_index, threshold):
        if not str(threshold) in self.correlations:
            return 0, 0
        if not int(field_index) in self.correlations[str(threshold)]:
            return 0, 0
        if not int(segment_index) in self.correlations[str(threshold)][int(field_index)]:
            return 0, 0
        return self.correlations[str(threshold)][int(field_index)][int(segment_index)]


def save(file_name, segments):
    json_object = SegmentEncoder().encode(segments)
    comp = zlib.compress(json_object.encode())
    with open(file_name, 'wb') as test_file:
        test_file.write(comp)


def load(file_name):
    with open(file_name, 'rb') as test_file:
        comp = test_file.read()
    test_file.close()
    comp = zlib.decompress(comp).decode()
    comp = SegmentDecoder().decode(comp)
    return comp


class SegmentEncoder(json.JSONEncoder):
    def encode_segment(self, obj):
        means = None
        if not isinstance(obj.means, list):
            means = obj.means.tolist()
        else:
            means = obj.means
        return json.JSONEncoder().encode({
            "is_leaf":obj.is_leaf,
            "children":list(map(int, obj.children)),
            "parent":int(obj.parent),
            "correlations":obj.correlations,
            "shape":obj.shape,
            "means":means,
            "color":obj.colors,
            "hulls":obj.hulls,
            "polygons":obj.polygons,
            "min":obj.min,
            "max":obj.max
        })

    def default(self, obj):
        if isinstance(obj, Segment):
            return self.encode_segment(obj)
        return json.JSONEncoder.default(self, obj)


class SegmentDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if isinstance(obj, dict):
            if("is_leaf" in obj and "children" in obj
                and "parent" in obj and "correlations" in obj
                and "shape" in obj and "color" in obj and "means" in obj):
                    s = Segment(obj.get("parent"), obj.get("children"), obj.get("shape"), obj.get("is_leaf"))
                    s.correlations = obj.get("correlations")
                    s.colors = obj.get("color")
                    s.means = obj.get("means")
                    if "hulls" in obj:
                        s.hulls = obj.get("hulls")
                    if "polygons" in obj:
                        s.polygons = obj.get("polygons")
                    if "min" in obj and "max" in obj:
                        s.min = obj.get("min")
                        s.max = obj.get("max")
                    return s
        # handling the resolution of nested objects
        if isinstance(obj, dict):
            for key in list(obj):
                if isinstance(key, str):
                    if key.isnumeric() and isinstance(obj[key], str):
                        obj[int(key)] = SegmentDecoder().decode(obj[key])#self.object_hook(obj[key])
                        del obj[key]
                    elif '.' in key or not key.isnumeric():
                        obj[key] = self.object_hook(obj[key])
                    else:
                        obj[int(key)] = self.object_hook(obj[key])
                        del obj[key]
            return obj

        if isinstance(obj, list):
            for i in range(0, len(obj)):
                obj[i] = self.object_hook(obj[i])
            return obj
        return obj
