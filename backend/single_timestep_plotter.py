import data_manager
import random
import utils as u
import matplotlib.pyplot as plt
import numpy as np

print("Moin")

#ENSEMBLE_INFOS = [("../testdata/real/rpc85/precipitation1", "pr", "precipitation")]
#ENSEMBLE_INFOS = [("../testdata/real/rpc85/temperature_surface1", "ts", "temperature_surface")]
#ENSEMBLE_INFOS = [("../testdata/real/rpc85/pressure_sea_level1", "psl", "pressure_sea_level")]
ENSEMBLE_INFOS = [("../testdata/artificial/artificialDataMix", "data", "mix1")]
#ENSEMBLE_INFOS = [("../testdata/artificial/artificialDataMix2", "data", "mix2")]

number_of_images = 3

# load Data
data = data_manager.load_ensembles_list(ENSEMBLE_INFOS, None)[0][0]

pos = int(random.uniform(0, data.shape[2]))

for i in range(0, number_of_images):

    data_i = data[:, :, pos + i]

    time_step = np.flip(u.normalize_point(data_i), axis=0)

    cmap = plt.cm.get_cmap('RdYlBu')
    norm = plt.Normalize(0, 1)

    # Create the plot and set the color map and normalization
    plt.imshow(1 - time_step, cmap=cmap, norm=norm)

    plt.axis("off")

    plt.savefig("../singleTimeStepPlots/" + ENSEMBLE_INFOS[0][2] + "" + str(i) + ".png")

print("Done with " + ENSEMBLE_INFOS[0][2])