# Visualization of Regional Time Series Correlation in Multi-field Ensembles
The tool provided in this repository, gives the opportunity to visualize correlations between multiple fields.

## Requirements
The dependencies for the python backend and preprocessing scripts can be installed by:
```
pip install numpy netCDF4 higra scipy PIL flask flask-cors matplotlib joblib
```

For the frontend, the only requirement is node.js (www.nodejs.org, tested on v12.22.9). Then switch to the 'frontend' folder and run:

```bash
# install dependencies
$ npm install
```

We tested this with the following dependencies:
```
    "@nuxtjs/axios": "^5.12.2",
    "bootstrap": "^4.5.3",
    "core-js": "^3.6.5",
    "d3": "^7.8.5",
    "hammerjs": "^2.0.8",
    "nuxt": "^2.14.6",
    "sass": "^1.29.0",
    "sass-loader": "^10.0.5"
```

For a detailed explanation of how things work, check out [Nuxt.js docs](https://nuxtjs.org).

## How to Run?
### Preprocessing
Switch to the 'backend' folder
1. Create similarity images
```
python multifield_correlate_multiple_fields.py
```
2. Create hierarchical segmentations
```
python preprocessing_segmentation.py
```
3. Add segment boundaries
```
python add_hulls.py
```
4. Add minimal and maximal correlation in each segment to evaluate smoothness (optional)
```
python add_minmax.py
```
5. Color the segments according to their mean color
```
python add_color.py
```
### Start the backend
Switch to the 'backend' folder and run
```
python api.py
```
By default, the API web server should run on port 5000. If this is not the case, you may need to change the `BACKEND_URL`-Variable in `frontend/store/vis.js` from `http://127.0.0.1:5000` to your local API address prompted in your Python console. 

### Start the frontend
Switch to the 'frontend' folder and run
```
# serve with hot reload at localhost:3000. Use this command for development.
$ npm run dev

# build for production and launch server
$ npm run build
$ npm run start

# generate static project
$ npm run generate
```

### Run with own data
An artificial dataset is provided in the repository, such that the tool can be executed and tested directly. However, it is also easy to apply it to own data.

The ensemble data should be in a folder where each subfolder contains a single ensemble member's data. Inside each folder, there is a single .nc file containing the spatial time series information.

To use your data, simply adapt the `ENSEMBLE_INFOS` variable in the `artificial_infos.py` to your data.
The other variables in the `artificial_infos.py` must also be adapted to fit your data and control the calculation.

## How to Use?
### Segmentation View
Hover: Highlight segment (linked to Correlation Heatmap) \
Shift + mouse left click: Select segment (linked to Correlation Heatmap and Statistics View) \
Shift + mouse left double click: Open pop up to assign a label to segment \
Filter selection button: Opens a new tab with similar views, but only the selected segments are available \
Refinement watershed level slider: Refines the selected segments to the chose watershed level

### Correlation Heatmap
Hover: Highlight segment (linked to Similarity Image) \
Shift + mouse left click: Select segment (linked to Segmentation View and Statistics View) \
Shift + mouse left drag: Select corresponding segments in the region (linked to Segmentation View and Statistics View) \
Correlation threshold: If more than one threshold was used in the precalculations, it could be selected here \
Linkage method: Choose the linkage method used for reordering the matrix based on hierarchical clustering \
Time Lags: Click 'show' to visualize the color-coded time lag in each cell. \
Mouse left click on color legends: Filter according to the correlation certainty or time lag respectively (linked to Correlation Heatmap and Statistics view)

### Statistics View
Mouse wheel: Zoom along the y-axis \
Hover over curve: Show value on the respective point
