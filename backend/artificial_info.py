# PATHS

#artificial data sets
ENSEMBLE_INFOS = [("../artificial_data/artificialData", "data", "artificial_data_1"),
                  ("../artificial_data/artificialData2", "data", "artificial_data_2")]

# Path to calculation data root
ROOT_PATH = '../tmp'

# Path to the correlations
CORR_PATH = ROOT_PATH + '/corr/'

# Path to the mds embeddings
MDS_PATH = ROOT_PATH + '/mds/'

# Path to the eigenvalues
EIGENS_PATH = ROOT_PATH + '/eigens/'

# Path to the segments
SEGMENTS_PATH = ROOT_PATH + '/segments/'


# OTHER

SHAPE = (256, 16, 24) # artificial data shape with width 24, height 16 and 256 time steps

# subsamples
subsample = None #switch according to wished subsample

# If the absolute value of the correlation exceeds this value, the time series are considered correlated.
# If more than one value is used, the user can switch interactively in the application (keep an eye on the memory for larger datasets)
THRESHOLDS = [0.9]

# Is the dataset periodic along the x-axis?
CIRCULAR = True

# If True, the Sobel filter is used for gradient calculations, otherwise the Euclidean distance
SOBEL = False

# Which maximal time lag should be taken into account?
MAX_TIME_LAG = 8

# Set to file with coastline overlay, if desired
COASTLINE = None

# What MDS to use? choose between: "normal" or the approximation "landmark"
MDS_VARIANT = "normal"
SAMPLESIZE = 0.5 # approx samplesize for landmark and pivot mds. Given in a Number between 0 and 1, which represents the percentage of the original Dataset.
