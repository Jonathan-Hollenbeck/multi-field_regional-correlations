import os
import netCDF4
import numpy as np
from netCDF4 import Dataset
import artificial_info as ai
import shutil
import matplotlib.pyplot as plt
import utils as u

from PIL import Image


def load_ensemble(ensemble_infos, subsample=None):
    number_of_runs = len(os.listdir(ensemble_infos[0]))
    if subsample is not None:
        ensemble = np.zeros((number_of_runs, subsample[1][0], subsample[1][1], subsample[1][2]))
    else:
        ensemble = np.zeros((number_of_runs, ai.SHAPE[1], ai.SHAPE[2], ai.SHAPE[0]))
    inner_counter = 0
    for run in os.listdir(ensemble_infos[0]):
        path = os.path.join(os.path.join(ensemble_infos[0], run), os.listdir(os.path.join(ensemble_infos[0], run))[0])
        f = netCDF4.Dataset(path)
        timelines = f.variables[ensemble_infos[1]]
        if subsample is None and timelines.shape != ai.SHAPE:
            print(u.colored_string("WARNING", "red") + ": Dataset shape: " + str(timelines.shape) + " does not match set shape: " + str(ai.SHAPE))
        timelines = np.transpose(timelines, axes=[1, 2, 0])
        # check if subsample is None and otherwise use it to subsample loaded data
        if subsample is not None:
            timelines = timelines[subsample[0][0], subsample[0][1], subsample[0][2]]
            if timelines.shape != subsample[1]:
                print(u.colored_string("WARNING", "red") + ": Dataset shape: " + str(timelines.shape) + " does not match set subsample shape: " + str(subsample[1]))
        ensemble[inner_counter] = timelines
        f.close()
        inner_counter += 1
    return ensemble


def remove_in_folder(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def save_data(data, path, shape, variable_name):
    ncout = Dataset(path, 'w', 'NETCDF3')
    ncout.createDimension('x', shape[0])
    ncout.createDimension('y', shape[1])
    ncout.createDimension('t', shape[2])
    xvar = ncout.createVariable('x', 'float32', ('x'))
    xvar[:] = np.arange(shape[0])
    yvar = ncout.createVariable('y', 'float32', ('y'))
    yvar[:] = np.arange(shape[1])
    timevar = ncout.createVariable('t', 'float32', ('t'))
    t = np.arange(shape[2])
    timevar[:] = t
    field = ncout.createVariable(variable_name, 'float32', ('t', 'x', 'y'))
    field[:] = data.transpose(2, 0, 1)
    ncout.close()


def save_mds_image(mds_points, field_index):
    mds_points = u.mds_image(mds_points, [ai.SHAPE[1], ai.SHAPE[2]])
    mds_img = (mds_points * 255).astype(np.uint8)
    mds_img = np.flip(mds_img, axis=0)
    im = Image.fromarray(mds_img)
    if ai.MDS_VARIANT == "normal":
        im.save("../mdsImages/" + str(ai.MDS_VARIANT) + "_" + str(ai.ENSEMBLE_INFOS[field_index][2]) + ".png", format='PNG')
    else:
        im.save("../mdsImages/" + str(ai.MDS_VARIANT) + "+" + str(ai.SAMPLESIZE) + "_" + str(ai.ENSEMBLE_INFOS[field_index][2]) + ".png", format='PNG')


def save_color_cloud_plot(mds_points, field_index):
    mds_points = u.mds_image(mds_points, [ai.SHAPE[1], ai.SHAPE[2]])
    mds_points = np.reshape(mds_points, (ai.SHAPE[1] * ai.SHAPE[2], mds_points.shape[-1]))
    mds_img = (mds_points * 255).astype(np.uint8)
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    ax.scatter(mds_points[:, 0], mds_points[:, 1], mds_points[:, 2], c=(mds_img.astype(np.float) / 255))

    if ai.MDS_VARIANT == "normal":
        plt.savefig("../colorClouds/" + str(ai.MDS_VARIANT) + "_" + str(ai.ENSEMBLE_INFOS[field_index][2]) + ".png")
    else:
        plt.savefig("../colorClouds/" + str(ai.MDS_VARIANT) + "+" + str(ai.SAMPLESIZE) + "_" + str(ai.ENSEMBLE_INFOS[field_index][2]) + ".png")