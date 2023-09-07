<template>
  <div class="card" style="user-select: none;">
    <h5 class="card-header"><a @click="invalidate">Correlation Heatmap</a>
      <span class="float-right"><small><a @click="show = !show"><span v-if="show">hide</span><span
              v-else>show</span></a></small></span>
    </h5>
    <div class="card-body" v-show="show">
      <div class="row">
        <a class="btn btn-secondary btn-sm" @click="selectAllSegmentsWithCorrelations">Select all Segments with correlations</a>
      </div>
      <div class="row">
        <div class="col-sm-2">
          <label>Correlation threshold</label>
          <select class="form-control" v-model="selectedThreshold"
            @change="$emit('change-threshold', selectedThreshold)">
            <option v-for="t in $store.state.vis.thresholds">{{ t }}</option>
          </select>
        </div>
        <div class="col-sm-3">
          <div class="form-group">
            <label>Linkage method</label>
            <select class="form-control" v-model="selectedLinkage" @change="$emit('change-linkage', selectedLinkage)">
              <option>single</option>
              <option>complete</option>
              <option>average</option>
              <option>centroid</option>
              <option>median</option>
              <option>ward</option>
            </select>
          </div>
        </div>
        <div class="col-sm-7">
          <label>Time lags <small>(<a @click="showTimeLags = true" v-if="!showTimeLags">show</a> <a
                @click="showTimeLags = false" v-else>hide</a>)</small></label>
          <transfer-function @value-selected="setSelectedTimelag" ref="transferFunction"
            :domain-from="$store.state.vis.timeLagRange[0]" :domain-to="$store.state.vis.timeLagRange[1]"
            transfer-function="interpolatePiYG"></transfer-function>
        </div>
      </div>
      <div style="display: flex; flex-flow:row wrap;">
        <div :style="`order: 1; height: 1rem; flex: 0 1 100%`">
          <div :style="`padding-left: 50px; display: flex; font-size: ${rectWidth}px;`">
            <div
              :style="`flex-direction:row; width: ${rectWidth}px; line-height:1; font-size: 0.7rem; text-align: center; color: ${getFontColor(0, rowSegment)};`"
              v-for="rowSegment in matrix.row_segments">
              <div style="width: 100%;">
                <div v-if="!labelsX[rowSegment]" style="transform: translateY(-2px) rotate(90deg); width: 0px; margin-left: 50%;">
                  {{ getLabelX(rowSegment) }}
                </div>
                <div v-else style="margin-left: 50%; color: black" v-bind:style="{'width': rectWidth + 'px',  transform: 'translate('+ (- rectWidth / 2) + 'px, -1em)'}">
                  {{ getLabelX(rowSegment) }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div :style="`order: 2; flex: 0 1 50px`">
          <div
            :style="`flex-direction:row; line-height:${rectHeight}px;  height:${rectHeight + 0.01}px; font-size: 0.7rem; text-align: center; color: ${getFontColor(1, colSegment)};`"
            v-for="colSegment in matrix.col_segments">
            <div v-if="!labelsY[colSegment]">
              {{ getLabelY(colSegment) }}
            </div>
            <div v-else style="color: black;">
              {{ getLabelY(colSegment) }}
            </div>
          </div>
        </div>
        <div :style="`order: 3; flex: 1; min-height:100px; width: calc(100% - 50px)`">
          <div ref="matrixWrapper" id="matrixWrapper"></div>
          <transfer-function @value-selected="correlationCertaintySelected" ref="transferFunctionCorr"
            :domain-from="-10" :domain-to="10" transfer-function="interpolateRdBu" :labels="['-1', '0', '1']"
            :title="'Correlation certainty'"></transfer-function>
          <!--          <transfer-function ref="transferFunctionTimeLag" :domain-from="$store.state.vis.timeLagRange[0]" :domain-to="$store.state.vis.timeLagRange[1]" transfer-function="interpolatePiYG" :title="'Time lag'"></transfer-function>-->

        </div>
      </div>
    </div>
    <div class="card-footer" v-show="show">
      <div class="row">
        <div class="col-sm-12">
          {{ infoText }}
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import * as d3 from "d3";
import SegmentFilter from "@/mixins/SegmentFilter";
import SegmentSelection from "@/mixins/SegmentSelection";
import TransferFunction from "./TransferFunction";

export default {
  components: { TransferFunction },
  props: {
    matrix: { type: Object, required: true },
    dimensions: { type: Array, required: true },
    linkage: { type: String, default: 'single' },
    threshold: { type: Number, default: 0.9 },
    highlightedSegmentsX: { type: Array, default: () => [] },
    highlightedSegmentsY: { type: Array, default: () => [] },
    labelsX: {
      type: Object, default: () => {
        return {}
      }
    },
    labelsY: {
      type: Object, default: () => {
        return {}
      }
    },
    t: {},
  },
  mixins: [SegmentFilter, SegmentSelection],
  data() {
    return {
      show: true,
      canvas: null,
      width: null,
      height: null,
      rectWidth: null,
      rectHeight: null,
      border: 5,
      isBrushing: false,
      brushStart: null,
      brushEnd: null,
      rects: [],
      highlightedSegmentsXLocal: [],
      highlightedSegmentsYLocal: [],
      highlightRowCol: [-1, -1],
      hoverValue: null,
      selectedLinkage: 'single',
      selectedThreshold: 0.9,
      time: 0,
      showTimeLags: false,
      infoText: '',
      selectedTimeLag: null,
      selectedTimeLagPrecise: false,
      selectedCorrelationCertainty: null,
      selectedCorrelationCertaintyPrecise: false,
    }
  },
  watch: {
    labelsX() {
      this.invalidate(false)
    },
    labelsY() {
      this.invalidate(false)
    },
    highlightedSegmentsY() {
      if(this.canvas != null){
        this.setHighlightedSegmentsRowCol();
        this.drawMatrix();
      }
    },
    highlightedSegmentsX() {
      if(this.canvas != null){
        this.setHighlightedSegmentsRowCol();
        this.drawMatrix();
      }
    },
    matrix: {
      deep: true,
      handler() {
        this.invalidate(true)
      }
    },
    showTimeLags() {
      this.invalidate(true)
    },
    linkage() {
      this.selectedLinkage = this.linkage
    }
  },
  computed: {
    brushTopLeft() {
      if (this.brushStart === null) return null
      let brushEnd = this.brushEnd;
      if (brushEnd === null) brushEnd = this.brushStart
      let fromRow = Math.min(this.brushStart[0], brushEnd[0]);
      let fromCol = Math.min(this.brushStart[1], brushEnd[1]);
      return [fromRow, fromCol]
    },
    brushBottomRight() {
      if (this.brushStart === null) return null
      let brushEnd = this.brushEnd;
      if (brushEnd === null) brushEnd = JSON.parse(JSON.stringify(this.brushStart))
      let toRow = Math.max(this.brushStart[0], brushEnd[0]);
      let toCol = Math.max(this.brushStart[1], brushEnd[1]);
      return [toRow, toCol]
    }
  },
  mounted() {
    window.addEventListener("resize", this.invalidate);
    this.selectedLinkage = this.linkage
    this.selectedThreshold = this.threshold
    this.invalidate()
  },
  methods: {
    drawMatrix() {
      const ctx = this.canvas.node().getContext('2d')
      ctx.save();
      let worldWidth = this.getWorldPosition(this.dimensions[0], this.dimensions[1])
      ctx.clearRect(0, 0, worldWidth[0], worldWidth[1])
      for (let i = 0; i < this.matrix.row_segments.length; i++) {
        for (let j = 0; j < this.matrix.col_segments.length; j++) {
          let corr = this.matrix.corrs[i][j]
          let timelag = this.matrix.time_lags[i][j]

          let checkDrawRect = this.checkDrawRect(corr, timelag)
          if(checkDrawRect){
            let worldPosition = this.getWorldPosition(i, j)
            let alpha = 1.
            ctx.fillStyle = this.addAlphaToRGBString(d3.interpolateRdBu((corr + 1) / 2), alpha)

            ctx.fillRect(worldPosition[0], worldPosition[1], this.rectWidth, this.rectHeight)

            if (this.showTimeLags && corr != 0) {
              ctx.fillStyle = this.addAlphaToRGBString(this.$refs.transferFunction.getColor(timelag), alpha * 255)
              ctx.fillRect(worldPosition[0] + this.rectWidth / 3, worldPosition[1] + this.rectHeight / 3, this.rectWidth / 4, this.rectHeight / 4)
            }
          }
        }
      }

      //highlight
      if(this.highlightRowCol != [-1, -1]){
        let worldPosition = this.getWorldPosition(this.highlightRowCol[0], this.highlightRowCol[1])
        ctx.fillStyle = "rgba(240, 0, 255, 0.3)"
        ctx.fillRect(0, worldPosition[1], this.rectWidth * this.matrix.row_segments.length, this.rectHeight)
        ctx.fillRect(worldPosition[0], 0, this.rectWidth, this.rectHeight * this.matrix.col_segments.length)
      }

      //current brushing
      ctx.fillStyle = 'rgba(0,0,0,0.3)'
      if (this.brushTopLeft && this.brushBottomRight) {
        let wpTopLeft = this.getWorldPosition(this.brushTopLeft[0], this.brushTopLeft[1])
        let wpBottomRight = this.getWorldPosition(this.brushBottomRight[0] + 1, this.brushBottomRight[1] + 1)
        ctx.fillRect(wpTopLeft[0], wpTopLeft[1], wpBottomRight[0] - wpTopLeft[0], wpBottomRight[1] - wpTopLeft[1])
      }

      //old brushes, who arent clicked away yet
      ctx.fillStyle = 'rgba(0,0,0,0.3)'
      for (let i = 0; i < this.rects.length; i++) {
        let r = this.rects[i]
        let wpTopLeft = this.getWorldPosition(r[0][0], r[0][1])
        let wpBottomRight = this.getWorldPosition(r[1][0] + 1, r[1][1] + 1)
        ctx.fillRect(wpTopLeft[0], wpTopLeft[1], wpBottomRight[0] - wpTopLeft[0], wpBottomRight[1] - wpTopLeft[1])
      }

      ctx.restore();
    },
    checkDrawRect(corr, timelag){
      if(this.selectedCorrelationCertainty != null){
        if(this.selectedCorrelationCertaintyPrecise){
          if(corr == this.selectedCorrelationCertainty){
            return true
          }
        }
        else{
          if(this.selectedCorrelationCertainty < 0){
            if(corr <= this.selectedCorrelationCertainty){
              return true
            }
          }
          else if(this.selectedCorrelationCertainty > 0){
            if(corr >= this.selectedCorrelationCertainty){
              return true
            }
          }
        }
      }
      else if(this.selectedTimeLag != null){
        if(this.selectedTimeLagPrecise){
          if(timelag == this.selectedTimeLag){
            return true
          }
        }
        else{
          if(this.selectedTimeLag < 0){
            if(corr <= this.selectedTimeLag){
              return true
            }
          }
          else if(this.selectedTimeLag > 0){
            if(corr >= this.selectedTimeLag){
              return true
            }
          }
        }
      }
      else {
        return true
      }
      return false
    },
    setHighlightedSegmentsRowCol(){
      let row = -1
      let col = -1
      for (let i = 0; i < this.matrix.row_segments.length; i++) {
        if(this.matrix.row_segments[i] == this.highlightedSegmentsX[0] && this.highlightedSegmentsX[0] != undefined){
          row = i
          break
        }
      }
      for (let i = 0; i < this.matrix.col_segments.length; i++) {
        if(this.matrix.col_segments[i] == this.highlightedSegmentsY[0] && this.highlightedSegmentsY[0] != undefined){
          col = i
          break
        }
      }
      this.highlightRowCol = [row, col]
    },
    getWorldPosition(row, col) {
      return [row * this.rectWidth, col * this.rectHeight]
    },
    getLocalPosition(x, y) {
      return [Math.floor(x / this.rectWidth), Math.floor(y / this.rectHeight)]
    },
    addAlphaToRGBString(rgbString, alpha = 1) {
      return rgbString.replace('rgb', 'rgba').substr(0, rgbString.length) + ', ' + alpha + ')'
    },
    invalidate(redraw = true) {
      setTimeout(() => {
        this.width = this.$refs.matrixWrapper.clientWidth
        this.height = this.width
        this.rectWidth = this.width / this.dimensions[0]
        this.rectHeight = this.height / this.dimensions[1]
        this.highlightedSegmentsXLocal = this.highlightedSegmentsX
        this.highlightedSegmentsYLocal = this.highlightedSegmentsY
        if (redraw) {
          d3.select(this.$refs.matrixWrapper).selectAll('*').remove()
          this.canvas = d3.select(this.$refs.matrixWrapper).append('canvas')
            .attr('width', JSON.parse(JSON.stringify(this.width)))
            .attr('height', JSON.parse(JSON.stringify(this.height)))
            .on('mousemove', this.onMouseMove)
            .on('mousedown', this.onMouseDown)
            .on('mouseup', this.onMouseUp)
            .on('mouseleave', this.onMouseLeave)
          this.drawMatrix()
        }
      }, 1)
    },
    selectAllSegmentsWithCorrelations(){
      let segmentsX = []
      let segmentsY = []
      for (let i = 0; i < this.matrix.row_segments.length; i++) {
        for (let j = 0; j < this.matrix.col_segments.length; j++) {
          if(this.matrix.corrs[i][j] != 0){
            segmentsX.push(this.matrix.row_segments[i])
            segmentsY.push(this.matrix.col_segments[j])
          }
        }
      }
      this.$emit('set-selected-segments', 0, segmentsX);
      this.$emit('set-selected-segments', 1, segmentsY);
    },
    getColor(value, row, col) {
      let color = d3.interpolateRdYlBu(value)
      let fill = `fill: ${color};`
      let opacity = '';
      return fill + opacity;
    },
    getLabelX(segment, defaultChar = null) {
      defaultChar = defaultChar || "█"
      if (!this.labelsX || Object.keys(this.labelsX).length === 0) return defaultChar
      return this.labelsX[segment] || defaultChar
    },
    getLabelY(segment, defaultChar = null) {
      defaultChar = defaultChar || "█"
      if (!this.labelsY || Object.keys(this.labelsY).length === 0) return defaultChar
      return this.labelsY[segment] || defaultChar
    },
    onMouseDown($event) {
      let mp = this.getMousePosition($event)
      let mpLocal = this.getLocalPosition(mp[0], mp[1])
      let row = mpLocal[0]
      let col = mpLocal[1]

      if ($event.shiftKey === false) {
        this.isBrushing = false;
        this.brushStart = null;
        this.brushEnd = null;
        this.$emit('set-selected-segments', 0, []);
        this.$emit('set-selected-segments', 1, []);
        this.rects = []
        this.selectedTimeLag = null
        this.selectedCorrelationCertainty = null
        this.selectedCorrelationCertaintyPrecise = false
        this.invalidate()
        return
      }
      this.isBrushing = true
      this.brushStart = [row, col]
      this.brushEnd = [row, col]
      this.drawMatrix()

      if ($event.shiftKey === false) {
        this.$emit('set-selected-segments', 0, []);
        this.$emit('set-selected-segments', 1, []);
        this.rects = []
      }
    },
    onMouseMove($event) {
      let mp = this.getMousePosition($event)
      let mpLocal = this.getLocalPosition(mp[0], mp[1])
      let row = mpLocal[0]
      let col = mpLocal[1]
      let row_segment = this.matrix.row_segments[row]
      let col_segment = this.matrix.col_segments[col]
      let time_lag = this.matrix.time_lags[row][col]
      if (!this.isBrushing) {
        this.$emit('highlight-segments-y', [col_segment])
        this.$emit('highlight-segments-x', [row_segment])
      } else {
        this.brushEnd = [row, col]
        this.drawMatrix()
      }
      this.infoText = `Segments: ${this.getLabelX(row_segment, row_segment)} & ${this.getLabelY(col_segment, col_segment)} - Correlation certainty: ${this.matrix.corrs[row][col]} -  Time lag: ${time_lag}`
    },
    onMouseUp($event) {
      if (this.isBrushing) {
        let selectedSegments = this.getBrushedSegments()
        if(this.selectedCorrelationCertainty != null || this.selectedTimeLag != null){
          this.$emit('set-selected-segments', 0, []);
          this.$emit('set-selected-segments', 1, []);
        }
        this.$emit('add-selected-segments', 0, selectedSegments[0])
        this.$emit('add-selected-segments', 1, selectedSegments[1])
        this.rects.push([this.brushTopLeft, this.brushBottomRight])
        this.isBrushing = false;
        this.brushStart = null;
        this.brushEnd = null;
      }
    },
    getBrushedSegments() {
      if (this.brushTopLeft === null || this.brushBottomRight === null) return []
      let selectedRowSegments = []
      let selectedColSegments = []
      selectedRowSegments = this.matrix.row_segments.slice(this.brushTopLeft[0], this.brushBottomRight[0] + 1);
      selectedColSegments = this.matrix.col_segments.slice(this.brushTopLeft[1], this.brushBottomRight[1] + 1);
      return [selectedRowSegments, selectedColSegments]
    },
    getMousePosition($event) {
      var rect = this.canvas.node().getBoundingClientRect();
      return [Math.floor($event.clientX - rect.left), Math.ceil($event.clientY - rect.top)]
    },
    onMouseLeave() {
      this.highlightRowCol = null
      this.$emit('highlight-segments-x', [])
      this.$emit('highlight-segments-y', [])
      this.infoText = ''
    },
    onResetSelection() {
      this.$emit('reset-segment-selection', 0)
      this.$emit('reset-segment-selection', 1)
      this.rects = []
    },
    getFontColor(axes, segment) {
      let c = 0
      if (axes == 0) {
        c = this.matrix.row_colors[segment]
      } else {
        c = this.matrix.col_colors[segment]
      }
      let style = `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
      return style
    },
    setSelectedTimelag($event, timelag) {
      this.selectedTimeLag = timelag
      let timelags = this.matrix.time_lags
      let corrs = this.matrix.corrs
      let rowSegments = this.matrix.row_segments
      let colSegments = this.matrix.col_segments
      let segmentsWithThisTimelagX = []
      let segmentsWithThisTimelagY = []
      for (let row = 0; row < timelags.length; row++) {
        for (let col = 0; col < timelags[row].length; col++) {
          if ($event.shiftKey) {
            this.selectedTimeLagPrecise = true
            if (timelags[row][col] == timelag) {
              if (corrs[row][col] != 0) {
                if (segmentsWithThisTimelagX.indexOf(rowSegments[row]) < 0) segmentsWithThisTimelagX.push(rowSegments[row])
                if (segmentsWithThisTimelagY.indexOf(colSegments[col]) < 0) segmentsWithThisTimelagY.push(colSegments[col])
              }
            }
          } else {
            this.selectedTimeLagPrecise = false
            if (timelag < 0) {
              if (timelags[row][col] <= timelag) {
                if (corrs[row][col] != 0) {
                  if (segmentsWithThisTimelagX.indexOf(rowSegments[row]) < 0) segmentsWithThisTimelagX.push(rowSegments[row])
                  if (segmentsWithThisTimelagY.indexOf(colSegments[col]) < 0) segmentsWithThisTimelagY.push(colSegments[col])
                }
              }
            } else if (timelag > 0) {
              if (timelags[row][col] >= timelag) {
                if (corrs[row][col] != 0) {
                  if (segmentsWithThisTimelagX.indexOf(rowSegments[row]) < 0) segmentsWithThisTimelagX.push(rowSegments[row])
                  if (segmentsWithThisTimelagY.indexOf(colSegments[col]) < 0) segmentsWithThisTimelagY.push(colSegments[col])
                }
              }
            }
          }
        }
      }
      this.$emit('set-selected-segments', 0, segmentsWithThisTimelagX);
      this.$emit('set-selected-segments', 1, segmentsWithThisTimelagY);
      this.drawMatrix()
    },
    correlationCertaintySelected($event, certainty) {
      certainty = certainty / 10
      this.selectedCorrelationCertainty = certainty
      let timelags = this.matrix.time_lags
      let corrs = this.matrix.corrs
      let rowSegments = this.matrix.row_segments
      let colSegments = this.matrix.col_segments
      let segmentsWithCertaintyX = []
      let segmentsWithCertaintyY = []
      for (let row = 0; row < timelags.length; row++) {
        for (let col = 0; col < timelags[row].length; col++) {
          if ($event.shiftKey) {
            this.selectedCorrelationCertaintyPrecise = true
            let r = Math.round(corrs[row][col] * 10) / 10
            if (r == certainty) {
              if (segmentsWithCertaintyX.indexOf(rowSegments[row]) < 0) segmentsWithCertaintyX.push(rowSegments[row])
              if (segmentsWithCertaintyY.indexOf(colSegments[col]) < 0) segmentsWithCertaintyY.push(colSegments[col])
            }
          } else {
            this.selectedCorrelationCertaintyPrecise = false
            if (certainty < 0) {
              if (corrs[row][col] <= certainty) {
                if (segmentsWithCertaintyX.indexOf(rowSegments[row]) < 0) segmentsWithCertaintyX.push(rowSegments[row])
                if (segmentsWithCertaintyY.indexOf(colSegments[col]) < 0) segmentsWithCertaintyY.push(colSegments[col])
              }
            } else if (certainty > 0) {
              if (corrs[row][col] >= certainty) {
                if (segmentsWithCertaintyX.indexOf(rowSegments[row]) < 0) segmentsWithCertaintyX.push(rowSegments[row])
                if (segmentsWithCertaintyY.indexOf(colSegments[col]) < 0) segmentsWithCertaintyY.push(colSegments[col])
              }
            }
          }
        }
      }
      this.$emit('set-selected-segments', 0, segmentsWithCertaintyX );
      this.$emit('set-selected-segments', 1, segmentsWithCertaintyY );
      this.drawMatrix()
    }
  }
}
</script>
