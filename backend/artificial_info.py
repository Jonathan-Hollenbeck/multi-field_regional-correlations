# PATHS

# Infos of ensemble data
#real world data sets
#ENSEMBLE_INFOS = [("../testdata/real/rcp85/precipitation10", "pr", "precipitation"),
#                  ("../testdata/real/rcp85/temperature_surface10", "ts", "temperature_surface"),
#                  ("../testdata/real/rcp85/pressure_sea_level10", "psl", "pressure_sea_level")]
ENSEMBLE_INFOS = [("../testdata/real/rcp85/pressure_sea_level_anomaly10", "psl", "pressure_sea_level_anomaly"),
                  ("../testdata/real/rcp85/temperature_surface_anomaly10", "ts", "temperature_surface_anomaly"),
                  ("../testdata/real/rcp85/precipitation_relative_anomaly10", "pr", "precipitation_relative_anomaly")]

#ENSEMBLE_INFOS = [("../GrandEnsemble/precipitation/rcp85", "pr", "precipitation"),
#                  ("../GrandEnsemble/temperature_surface/rcp85", "ts", "temperature_surface"),
#                  ("../GrandEnsemble/pressure_sea_level/rcp85", "psl", "pressure_sea_level")]
#ENSEMBLE_INFOS = [("../GrandEnsemble/pressure_sea_level_anomaly/rcp85", "psl", "pressure_sea_level_anomaly"),
#                  ("../GrandEnsemble/temperature_surface_anomaly/rcp85", "ts", "temperature_surface_anomaly"),
#                  ("../GrandEnsemble/precipitation_relative_anomaly/rcp85", "pr", "precipitation_relative_anomaly")]

#ENSEMBLE_INFOS = [("../testdata/real/rpc85/temperature_surface1", "ts", "temperature_surface")]


#artificial data sets
#ENSEMBLE_INFOS = [("../testdata/artificial/artificialDataMix", "data", "mix1"),
#                  ("../testdata/artificial/artificialDataMix2", "data", "mix2")]
#ENSEMBLE_INFOS = [("../testdata/artificial/artificialDataCircular", "data", "circular1"),
#                  ("../testdata/artificial/artificialDataCircular2", "data", "circular2")]
#ENSEMBLE_INFOS = [("../testdata/artificial/artificialDataHoles", "data", "holes1"),
#                  ("../testdata/artificial/artificialDataHoles2", "data", "holes2")]
#ENSEMBLE_INFOS = [("../testdata/artificial/artificialHullsShow", "data", "sobel")]

# Path to data root
#ROOT_PATH = '../tmp'
#ROOT_PATH = '../../world_normal_pr_ts_psl'
ROOT_PATH = '../../world_anomalies_pr_ts_psl'
#ROOT_PATH = '../../testbase'

# Path to the correlations
CORR_PATH = ROOT_PATH + '/corr/'

# Path to the mds embeddings
MDS_PATH = ROOT_PATH + '/mds/'

# Path to the eigenvalues
EIGENS_PATH = ROOT_PATH + '/eigens/'

# Path to the segments
SEGMENTS_PATH = ROOT_PATH + '/segments/'


# OTHER

# Shape of the data, where the first number indicate number of timesteps
SHAPE = (1128, 96, 192) # world
#SHAPE = (1128, 20, 24) # europe subsample

#SHAPE = (256, 16, 24) # artificial Mix
#SHAPE = (128, 30, 30) # artificial Circular
#SHAPE = (100, 12, 12) # artificial Holes
#SHAPE = (100, 8, 15) # artificial Hulls show

# europes latitude and longitude on the Grandensemble dataset
EUROPE_LAT = slice(67, 87)
EUROPE_LON = list(range(186, 192)) + list(range(0, 18))

# subsamples
subsample_europe = ((EUROPE_LAT, EUROPE_LON, slice(1128)), (20, 24, 1128)) # 20*24
subsample_slice_time = ((slice(SHAPE[1]), slice(SHAPE[2]), slice(100)), (96, 192, 100))
subsample = None #switch according to wished subsample

# If the absolute value of the correlation exceeds this value, the time series are considered correlated.
# If more than one value is used, the user can switch interactively in the application (keep an eye on the memory for larger datasets)
THRESHOLDS = [0.3]

# Is the dataset periodic along the x-axis?
CIRCULAR = True

# If True, the Sobel filter is used for gradient calculations, otherwise the Euclidean distance
SOBEL = True

# Which maximal time lag should be taken into account?
MAX_TIME_LAG = 12

# Set to file with coastline overlay, if desired
COASTLINE = "../coastline.png"

# What MDS to use? choose between: "normal" or the approximation "landmark"
MDS_VARIANT = "landmark"
SAMPLESIZE = 0.5 # approx samplesize for landmark and pivot mds. Given in a Number between 0 and 1, which represents the percentage of the original Dataset.