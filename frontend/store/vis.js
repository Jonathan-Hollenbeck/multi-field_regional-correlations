import Vue from 'vue'

const BACKEND_URL = 'http://127.0.0.1:5000'

export const state = () => ({
  history: [],
  thresholds: [],
  overviews: {
    "1": {
      isActive: true,
      correlationMatrix: {},
      segmentationX: {},
      segmentationY: {},
      selectedSegmentsX: {},
      selectedSegmentsY: {},
      filteredSegmentsX: {},
      filteredSegmentsY: {},
      labelsX: {},
      labelsY: {},
      labelsByFieldName: {},
      maxWatershedLevelX: 100,
      maxWatershedLevelY: 100,
      treeHeightX: 100,
      treeHeightY: 100,
      mdsImage: null,
      curves: {},
      selectedFieldX: "X",
      selectedFieldY: "Y"
    }
  },
  activeOverviewTab: "1",
  t: 0,
  overlay: null,
  timeLagRange: [0, 1],
  swapHalf: false,
  numberOfFields: 0,
  fieldNames: []
})

export const actions = {
  resetSegmentSelection({ state, commit, dispatch }, { axis, level, segment }) {
    if(axis == 0){
      commit('updateOverview', { level, key: 'selectedSegmentsX', value: {} })
    }
    else{
      commit('updateOverview', { level, key: 'selectedSegmentsY', value: {} })
    }
  },
  setSelectedSegments({ state, commit, dispatch }, { axis, level, segments }) {
    if (axis == 0) {
      commit('updateOverview', { level, key: 'selectedSegmentsX', value: Object.assign({}, ...segments.map((s) => ({ [s]: true }))) })
    }
    else {
      commit('updateOverview', { level, key: 'selectedSegmentsY', value: Object.assign({}, ...segments.map((s) => ({ [s]: true }))) })
    }
  },
  addSelectedSegment({ state, commit, dispatch }, { axis, level, segment }) {
    if (axis == 0) {
      let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegmentsX))
      selectedSegments[segment] = true
      commit('updateOverview', { level, key: 'selectedSegmentsX', value: selectedSegments })
    }
    else {
      let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegmentsY))
      selectedSegments[segment] = true
      commit('updateOverview', { level, key: 'selectedSegmentsY', value: selectedSegments })
    }
  },
  addSelectedSegments({ state, commit, dispatch }, { axis, level, segments }) {
    if (axis == 0) {
      let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegmentsX))
      for (let s in segments) {
        selectedSegments[segments[s]] = true
      }
      commit('updateOverview', { level, key: 'selectedSegmentsX', value: selectedSegments })
    }
    else {
      let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegmentsY))
      for (let s in segments) {
        selectedSegments[segments[s]] = true
      }
      commit('updateOverview', { level, key: 'selectedSegmentsY', value: selectedSegments })
    }
  },
  removeSelectedSegment({ state, commit, dispatch }, { axis, level, segment }) {
    if (axis == 0) {
      let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegmentsX))
      delete selectedSegments[segment]
      commit('updateOverview', { level, key: 'selectedSegmentsX', value: selectedSegments })
    }
    else {
      let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegmentsY))
      delete selectedSegments[segment]
      commit('updateOverview', { level, key: 'selectedSegmentsY', value: selectedSegments })
    }
  },
  assignSegmentLabel({ state, commit }, { axis, level, segment, label, fieldName }) {
    if (axis == 0) {
      let labels = JSON.parse(JSON.stringify(state.overviews[level].labelsX))
      labels[segment] = label
      commit('updateOverview', { level, key: 'labelsX', value: labels })
    }
    else {
      let labels = JSON.parse(JSON.stringify(state.overviews[level].labelsY))
      labels[segment] = label
      commit('updateOverview', { level, key: 'labelsY', value: labels })
    }
    let labelsByFieldName = JSON.parse(JSON.stringify(state.overviews[level].labelsByFieldName))
    if(labelsByFieldName[fieldName] == undefined){
      labelsByFieldName[fieldName] = {}
    }
    labelsByFieldName[fieldName][segment] = label
    commit('updateOverview', { level, key: 'labelsByFieldName', value: labelsByFieldName })
  },
  filterSelection({ state, commit }, { level }) {
    let newOverview = JSON.parse(JSON.stringify(state.overviews[level]))
    newOverview.filteredSegmentsX = {}
    newOverview.filteredSegmentsY = {}
    newOverview.curves = {}
    if(Object.keys(state.overviews[level].selectedSegmentsX).length == 0){
      for (let s in state.overviews[level].correlationMatrix.matrix.row_segments) {
        let ss = state.overviews[level].correlationMatrix.matrix.row_segments[s]
        newOverview.filteredSegmentsX[ss] = true
      }
    } else {
      for (let s in state.overviews[level].selectedSegmentsX) {
        newOverview.filteredSegmentsX[s] = true
      }
    }
    if(Object.keys(state.overviews[level].selectedSegmentsY).length == 0){
      for (let s in state.overviews[level].correlationMatrix.matrix.col_segments) {
        let ss = state.overviews[level].correlationMatrix.matrix.col_segments[s]
        newOverview.filteredSegmentsY[ss] = true
      }
    } else {
      for (let s in state.overviews[level].selectedSegmentsY) {
        newOverview.filteredSegmentsY[s] = true
      }
    }
    let highestLevel = Math.max(...Object.keys(state.overviews).map(k => parseInt(k)))
    newOverview.level = parseInt(highestLevel) + 1
    newOverview.selectedSegmentsX = {}
    newOverview.selectedSegmentsY = {}
    commit('createOverview', { level: newOverview.level, newOverview })

    return newOverview
  },
  setOverviewTab({ state, commit }, level) {
    commit('activeOverviewTab', level)
  },
  removeOverview({ state, commit }, level) {
    let confi = confirm('Do you really want to close this view?')
    if (!confi) return
    let o = JSON.parse(JSON.stringify(state.overviews))
    delete o[level]
    commit('overviews', o)
    commit('activeOverviewTab', parseInt(level) - 1)
  },
  loadSegmentation({ state, commit }, { axis, level, watershedLevel, name }) {
    return this.$axios.get(BACKEND_URL + '/get-segments-by-watershed-level/' + axis + "/" + watershedLevel + "/" + name).then(
      response => {
        if (axis == 0) {
          commit('updateOverview', { level, key: 'segmentationX', value: response.data })
          commit('updateOverview', { level, key: 'selectedFieldX', value: response.data.name })
        } else {
          commit('updateOverview', { level, key: 'segmentationY', value: response.data })
          commit('updateOverview', { level, key: 'selectedFieldY', value: response.data.name })
        }
      }
    )
  },
  loadCorrelationMatrix({ state, commit }, { level, watershedLevelX, watershedLevelY, segmentsX, segmentsY }) {
    let link = state.overviews[level].correlationMatrix.linkage ? state.overviews[level].correlationMatrix.linkage : process.env.defaultLinkage
    let threshold = state.overviews[level].correlationMatrix.threshold ? state.overviews[level].correlationMatrix.threshold : process.env.defaultThreshold
    let url = ""
    url = `${BACKEND_URL}/get-correlation-matrix-by-watershed-level/${watershedLevelX}/${watershedLevelY}/${threshold}/${link}`

    if (segmentsX != undefined && segmentsY != undefined) {
      let loadedSegmentsX = state.overviews[level].segmentationX.segments ? state.overviews[level].segmentationX.segments.map(s => s.segment) : []
      let sx = loadedSegmentsX
      if (Object.keys(state.overviews[level].filteredSegmentsX).length > 0) {
        sx = Object.keys(state.overviews[level].filteredSegmentsX)
      }
      if (segmentsX) {
        sx = segmentsX
      }

      let loadedSegmentsY = state.overviews[level].segmentationY.segments ? state.overviews[level].segmentationY.segments.map(s => s.segment) : []
      let sy = loadedSegmentsY
      if (Object.keys(state.overviews[level].filteredSegmentsY).length > 0) {
        sy = Object.keys(state.overviews[level].filteredSegmentsY)
      }
      if (segmentsY) {
        sy = segmentsY
      }

      if (sx.length > 0) url += `/${sx.join(',')}`
      if (sy.length > 0) url += `/${sy.join(',')}`
    }

    return this.$axios.get(url).then(
      response => {
        if (response.data === null) {
          return
        }
        commit('updateOverview', { level, key: 'correlationMatrix', value: response.data })
      }
    )
  },
  changeCorrelationMatrixLinkage({ state, commit, dispatch }, { level, linkage }) {
    let correlationMatrix = JSON.parse(JSON.stringify(state.overviews[level].correlationMatrix))
    correlationMatrix.linkage = linkage
    commit('updateOverview', { level, key: 'correlationMatrix', value: correlationMatrix })

    return linkage
  },
  changeCorrelationMatrixThreshold({ state, commit, dispatch }, { level, threshold }) {
    let correlationMatrix = JSON.parse(JSON.stringify(state.overviews[level].correlationMatrix))
    correlationMatrix.threshold = threshold
    commit('updateOverview', { level, key: 'correlationMatrix', value: correlationMatrix })

    return threshold
  },
  refineSegments({ state, commit, dispatch }, { axis, level, segments, watershedLevelX, watershedLevelY }) {
    let watershedLevel = null
    if(axis == 0)
      watershedLevel = watershedLevelX
    else
      watershedLevel = watershedLevelY
    this.$axios.get(`${BACKEND_URL}/refine-segment/${axis}/${Object.keys(segments).join(',')}/${watershedLevel}`).then(
      response => {
        //make copies from current segmentation and delete the selected segments
        let segmentationX = JSON.parse(JSON.stringify(state.overviews[level].segmentationX))
        segmentationX.segments = state.overviews[level].segmentationX.segments.filter(s => !segments[s.segment])
        let filteredX = JSON.parse(JSON.stringify(state.overviews[level].filteredSegmentsX))

        let segmentationY = JSON.parse(JSON.stringify(state.overviews[level].segmentationY))
        segmentationY.segments = state.overviews[level].segmentationY.segments.filter(s => !segments[s.segment])
        let filteredY = JSON.parse(JSON.stringify(state.overviews[level].filteredSegmentsY))

        let newSegments = response.data.segments

        if(axis == 0){
          //add new Segments to filtered list and to segmentation
          for (let i = 0; i < newSegments.length; i++) {
            let s = newSegments[i]
            filteredX[s.segment] = true
            segmentationX.segments.push(s)
          }
          //update overview with new segments
          if (Object.keys(state.overviews[level].filteredSegmentsX).length > 0)
            commit('updateOverview', { level, key: 'filteredSegmentsX', value: filteredX })
          commit('updateOverview', { level, key: 'segmentationX', value: segmentationX })
        }
        else {
          //add new Segments to filtered list and to segmentation
          for (let i = 0; i < newSegments.length; i++) {
            let s = newSegments[i]
            filteredY[s.segment] = true
            segmentationY.segments.push(s)
          }
          //update overview with new segments
          if (Object.keys(state.overviews[level].filteredSegmentsY).length > 0)
            commit('updateOverview', { level, key: 'filteredSegmentsY', value: filteredY })
          commit('updateOverview', { level, key: 'segmentationY', value: segmentationY })
        }

        let allSegmentsX = []
        let allSegmentsY = []

        //add segment names to list
        for(let i in segmentationX.segments) {
          allSegmentsX.push(segmentationX.segments[i].segment)
        }
        for(let i in segmentationY.segments) {
          allSegmentsY.push(segmentationY.segments[i].segment)
        }

        //update matrixview
        dispatch('loadCorrelationMatrix', {
          level,
          watershedLevelX,
          watershedLevelY,
          segmentsX: allSegmentsX,
          segmentsY: allSegmentsY
        })

        //set selected Segments, to refined Segments
        dispatch('setSelectedSegments', { axis, level, segments: newSegments.map(s => s.segment) })

        commit('pushHistory')
      }
    )
  },
  undo({ state, commit }) {
    if (state.history.length === 0) return

    let nextState = state.history[state.history.length - 1]
    // if(Object.keys(nextState[0].segmentation).length === 0) return
    let overviews = JSON.parse(JSON.stringify(nextState))
    commit('undo', overviews)
  },
  fetchThresholds({ state, commit }) {
    this.$axios.get(BACKEND_URL + '/get-thresholds').then(
      response => {
        commit('thresholds', response.data)
      }
    )
  },
  fetchDetails({ state, commit }, { axis, level }) {
    let segments = null;
    
    if(axis == 0){
      if(Object.keys(state.overviews[level].filteredSegmentsX).length != 0){
        segments = Object.keys(state.overviews[level].filteredSegmentsX)
      }
      else{
        segments = Object.keys(state.overviews[level].selectedSegmentsX)
      }
    }
    else{
      if(Object.keys(state.overviews[level].filteredSegmentsX).length != 0){
        segments = Object.keys(state.overviews[level].filteredSegmentsY)
      }
      else{
        segments = Object.keys(state.overviews[level].selectedSegmentsY)
      }
    }

    let curves = {}

    if (segments.length > 0){
      this.$axios.get(BACKEND_URL + '/get-curves-for-segments/' + axis + "/" + segments.join(',')).then(
        response => {
          curves = response.data
          let newCurves = state.overviews[level].curves
          //loop throu fields
          for (let i in curves) {
            //loop throu segments
            for(let j in curves[i]){
              if(newCurves[i] == undefined){
                newCurves[i] = {}
              }
              if(newCurves[i][j] == undefined){
                newCurves[i][j] = curves[i][j]
              }
            }
          }
          commit('updateOverview', { level, key: 'curves', value: newCurves })
        }
      )
    }
  },
  resetDetails({state, commit}, {level}){
    commit('updateOverview', { level, key: 'curves', value: {} })
  },
  getMdsImage({ state, commit }, {level, selectedField}) {
    this.$axios(BACKEND_URL + '/get-mds-image/' + selectedField + '/' + state.swapHalf).then(
      response => {
        commit('updateOverview', { level, key: 'mdsImage', value: response.data.image })
        commit('overlay', response.data.overlay)
      }
    )
  },
  timeLagRange({ state, commit }) {
    this.$axios.get(BACKEND_URL + '/get-time-lag-range').then(
      response => {
        commit('timeLagRange', response.data)
      }
    )
  },
  swapHalf({ state, commit, dispatch }, swapHalf) {
    commit('swapHalf', swapHalf)
    dispatch('getMdsImage')
  },
  getNumberOfFields({ state, commit }) {
    this.$axios(BACKEND_URL + "/get-number-of-fields").then(
      response => {
        commit('numberOfFields', response.data)
      }
    )
  },
  getFieldNames({ state, commit }) {
    this.$axios(BACKEND_URL + "/get-field-names").then(
      response => {
        commit('fieldNames', response.data)
      }
    )
  },
  getTreeHeight({ state, commit}, {axis, level} ) {
    this.$axios(BACKEND_URL + "/get-tree-height/" + axis).then(
      response => {
        if( axis == 0 ){
          commit('updateOverview', { level, key: 'treeHeightX', value: response.data })
        }
        else {
          commit('updateOverview', { level, key: 'treeHeightY', value: response.data })
        }
      }
    )
  },
  getMaxWatershedLevel({ state, commit}, {axis, level} ) {
    this.$axios(BACKEND_URL + "/get-max-watershed-level/" + axis).then(
      response => {
        if( axis == 0 ){
          commit('updateOverview', { level, key: 'maxWatershedLevelX', value: response.data })
        }
        else {
          commit('updateOverview', { level, key: 'maxWatershedLevelY', value: response.data })
        }
      }
    )
  }
}

export const mutations = {
  overviews(state, overviews) {
    state.history.push(state.overviews)
    state.overviews = overviews;
    state.t += 1
  },
  thresholds(state, thresholds) {
    state.thresholds = thresholds;
    state.t += 1
  },
  undo(state, overviews) {
    state.overviews = overviews;
    state.history.pop()
    state.t += 1
  },
  activeOverviewTab(state, activeOverviewTab) {
    state.activeOverviewTab = activeOverviewTab
    state.t += 1
  },
  updateOverview(state, { level, key, value }) {
    Vue.set(state.overviews[level], key, value)
    state.t += 1
  },
  pushHistory(state) {
    state.history.push(state.overviews)
    state.t += 1
  },
  removeOverview(state, level) {
    state.overviews[level].isActive = false
    state.t += 1
  },
  createOverview(state, { level, newOverview }) {
    state.overviews[level] = newOverview
    state.activeOverviewTab = level
    state.t += 1
  },
  hideOverview(state, level) {
    state.overviews[level].isActive = false
    state.t += 1
  },
  timeLagRange(state, range) {
    state.timeLagRange = range
  },
  swapHalf(state, swapHalf) {
    state.swapHalf = swapHalf
  },
  overlay(state, overlay) {
    state.overlay = overlay
  },
  numberOfFields(state, number) {
    state.numberOfFields = number
  },
  fieldNames(state, names) {
    state.fieldNames = names
  }
}
