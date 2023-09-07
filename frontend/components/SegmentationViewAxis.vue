<template>
  <div class="card" style="user-select: none">
    <h5 class="card-header">
      <a @click="invalidate">{{ title }}</a>
      <span class="float-right"><small><a @click="show = !show"><span v-if="show">hide</span><span
              v-else>show</span></a></small></span>
    </h5>
    <div class="col-sm" v-show="show">
      <select class="form-control" v-model="selectedFieldLocal"
        @change="$emit('load-segmentation', axis, watershedLevel, selectedFieldLocal)" :disabled="isFiltered">
        <option v-for="field in fieldNames">{{ field }}</option>
      </select>
    </div>
    <div ref="segmentCanvasWrapper" class="card-body" v-show="show">
      <span v-show="false">{{ t }}</span>
      <div class="row">
        <div class="row">
          <div class="col-sm-9">
            <div class="form-group">
              <label for="formControlRange">Watershed level ({{ watershedLevel }})</label>
              <input type="range" class="form-control-range" id="formControlRange" v-model="watershedLevel" @change="
                $emit('load-segmentation', axis, watershedLevel, selectedFieldLocal)"
                :max="maxWatershedLevel" />
            </div>
          </div>
          <div class="col-sm">
            <input v-model="watershedLevel" @change="$emit('load-segmentation', axis, watershedLevel, selectedFieldLocal)"
              class="form-control" />
          </div>
        </div>
      </div>
      <div class="row">
        <segment-refinement v-show="hasSelection" :axis="axis" :segments="selectedSegments" :init-watershed-level="watershedLevel"
          @refine-segments="$emit('refine-segments', $event)"></segment-refinement>
      </div>
      <div class="row text-right">{{ segmentCount }} segments<label v-if="$store.state.vis.overlay"><input type="checkbox" v-model="showOverlay"> Show overlay</label></div>
      <!--<div class="row text-right">{{ treeHeight }} tree height</div>-->

      <svg :viewBox="`0 0 ${dimensions[1]} ${dimensions[0]}`" :width="width" :height="height"
        :style="isRotated ? 'transform: rotate(180deg) scaleX(-1) translate(-20px, 0px)' : null"
        @mouseleave="$emit('highlight-segments', [])">
        <g v-for="segment in segments_render" :style="getSegmentColor(segment)"
        @click="onSegmentClicked($event, segment.segment)" @mouseover="onSegmentMouseOver($event, segment.segment)">
          <polygon v-for="polygon in segment.polygon" :points="polygonPointString(polygon)"></polygon>
        </g>
        <g v-for="segment in segments_render"
        @click="onSegmentClicked($event, segment.segment)" @mouseover="onSegmentMouseOver($event, segment.segment)">
          <polyline v-for="hull in segment.hull" :points="hullPointString(hull)"
          :style="labels[segment.segment] ? 'fill: none; stroke: black; stroke-width: 0.5; stroke-dasharray:2,0.5;' : 'fill: none; stroke: white; stroke-width: 0.1;'"/>
        </g>

        <image :href="'data:image/png;base64,' + $store.state.vis.overlay"
          :style="{width: dimensions[1] + 'px', height: dimensions[0] + 'px', transform: 'rotate(180deg) scaleX(-1) scaleY(1.03) translate(0.8px, -' + (dimensions[0] - 1) + 'px)'}" v-if="showOverlay"/>
      </svg>

      

      <segment-label-modal @close="resetSegementLabel" @okay="assignLabel" v-if="selectedSegment !== null"
        :selected-segment="selectedSegment" :selected-segment-label="selectedSegmentLabel"></segment-label-modal>

      <modal v-if="showSegmentTable" @close="showSegmentTable = null" @okay="showSegmentTable = null">
        <div slot="body">
          <table class="table">
            <tr>
              <th style="height: 50px">Segment</th>
              <th>
                Label
                <small><a @click="tableLabeledOnly = !tableLabeledOnly">only</a></small>
              </th>
              <th>&nbsp;</th>
            </tr>
            <tr v-for="segment in segments" v-if="!tableLabeledOnly || labels[segment] !== undefined"
              :class="{ 'table-secondary': selectedSegments[segment.segment] === true }"
              @mouseover="$emit('highlight-segments', [segment.segment])"
              @mouseleave="$emit('highlight-segments', [])">
              <td>{{ segment.segment }}</td>
              <td>
                <input class="form-control" :value="labels[segment.segment]"
                  @input="assignLabel(segment.segment, $event.target.value)" />
              </td>
              <td class="text-right">
                <a v-if="selectedSegments[segment.segment] !== true" class="btn btn-success btn-sm"
                  @click="$emit('add-selected-segment', axis, segment.segment)">select</a>
                <a v-else class="btn btn-danger btn-sm"
                  @click="$emit('remove-segment-selection', axis, segment.segment)">unselect</a>
              </td>
            </tr>
          </table>
        </div>
      </modal>
    </div>
    <div class="card-footer" v-show="show">
      <div class="row">
        <div class="col-sm-9">
          {{ hoverLabel }} Min:{{ hoverMin }}, Max:{{ hoverMax }}
        </div>
      </div>
      <div class="row">
        <div class="col-sm-12">
          <div class="text-right">
            <div class="btn-group">
              <a class="btn btn-sm btn-secondary" @click="$emit('reset-segment-selection', axis)" v-if="hasSelection">Reset
                selection</a>
              <a class="btn btn-sm btn-info" @click="$emit('filter-selection')" v-if="hasSelection">Filter selection</a>
              <a class="btn btn-sm btn-success" @click="showSegmentTable = !showSegmentTable">Show table</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import * as d3 from "d3";
import Modal from "./Modal";
import SegmentLabelModal from "./SegmentLabelModal";
import SegmentFilter from "@/mixins/SegmentFilter";
import SegmentSelection from "@/mixins/SegmentSelection";
import SegmentRefinement from "./SegmentRefinement";
import internal from "stream";

export default {
  components: { SegmentRefinement, SegmentLabelModal, Modal },
  props: {
    title: { type: String, default: "Segmentation View" },
    axis: { type: Number, default: 0 },
    segmentation: { type: Object, default: () => {} },
    highlightedSegments: { type: Array, default: () => [] },
    labels: { type: Object, default: () => {} },
    maxWatershedLevel: { type: Number, required: true },
    treeHeight: { type: Number, required: true },
    fieldNames: { type: Array, required: true },
    selectedField: {type: String},
    t: {},
  },
  mixins: [SegmentFilter, SegmentSelection],
  data() {
    return {
      show: true,
      height: null,
      width: null,
      selectedSegment: null,
      selectedSegmentLabel: null,
      showSegmentTable: false,
      hoverLabel: null,
      hoverMin: null,
      hoverMax: null,
      tableLabeledOnly: false,
      clicks: 0,
      timer: null,
      watershedLevel: process.env.initWatershedLevel,
      selectedFieldLocal: null,
      segments: [],
      dimensions: [],
      showOverlay: false
    };
  },
  computed: {
    segments_render() {
      let segments_render = [];
      for (let i = 0; i < this.segments.length; i++) {
        let segment = this.segments[i]
        if(this.labels[segment.segment]) {
          segments_render.push(segment);
        }
        else {
          segments_render.unshift(segment)
        }
      }
      return segments_render;
    },
    isRotated() {
      return process.env.isRotated;
    },
    segmentCount() {
      return this.segments.length;
    },
  },
  watch: {
    segmentation() {
      this.segments = this.segmentation.segments
      this.dimensions = this.segmentation.dimensions
      this.invalidate();
    },
    selectedSegments() {
      this.invalidate();
    },
    highlightedSegments() {
      this.invalidate();
      this.updateHoverLabels(this.highlightedSegments[0])
    },
    labels() {
      this.invalidate();
    },
    selectedField(){
      this.selectedFieldLocal = this.selectedField
    }
  },
  mounted() {
    window.addEventListener("resize", this.invalidate);
    this.invalidate();
    this.selectedFieldLocal = this.selectedField
    this.segments = this.segmentation.segments
    this.dimensions = this.segmentation.dimensions
    this.watershedLevel = this.segmentation.watershed_level
  },
  methods: {
    invalidate() {
      this.width = this.$refs.segmentCanvasWrapper.clientWidth;
      this.height = (this.dimensions[0] + 1) * (this.width / (this.dimensions[1] + 1));
    },
    polygonPointString(segmentPolygon) {
      return segmentPolygon
        .map((d) => {
          return [d[0], d[1]];
        })
        .join(" ");
    },
    hullPointString(segmentHull) {
      let map = segmentHull
        .map((d) => {
          return [d[0], d[1]];
        })
      map.push(map[0])
      return map.join(" ")
    },
    getSegmentColor(segment) {
      let color = `rgba(${segment.color[0]},${segment.color[1]},${segment.color[2]},${segment.color[3]});`;

      //turn down color opacity if not filtered
      if (Object.keys(this.filteredSegments).length > 0 &&
        this.filteredSegments[segment.segment] !== true)
        color = "rgba(0,0,0,0.02)";

      //fill color
      let fill = `fill: ${color};`;

      //turn down opacity if not selected
      if (this.hasSelection && !this.selectedSegments[segment.segment])
        fill = `fill: ${color}; opacity: 0.2;`;

      //highlighting
      if (this.highlightedSegments !== null && 
        this.highlightedSegments.indexOf(segment.segment) >= 0)
        fill = "fill: #f000ff;";
        
      return fill;
    },
    onSegmentClicked(e, segment) {
      this.clicks++;
      if (this.clicks === 1) {
        this.timer = setTimeout(() => {
          this.onSegmentSingleClicked(e, segment);
          this.clicks = 0;
        }, 200);
      } else {
        clearTimeout(this.timer);
        this.onSegmentDoubleClicked(e, segment);
        this.clicks = 0;
      }
    },
    onSegmentSingleClicked(e, segment) {
      if (this.selectedSegments[segment] === true) {
        // if already selected, unselect
        if (e.shiftKey) {
          this.$emit("remove-segment-selection", this.axis, segment);
        }
      } else {
        if (e.shiftKey) {
          this.$emit("add-selected-segment", this.axis, segment);
        }
      }
    },
    onSegmentDoubleClicked(e, segment) {
      this.selectedSegment = segment;
      this.selectedSegmentLabel = this.labels[segment] || null;
    },
    assignLabel(segment, label) {
      // if (segment === null || label === null || label === '') return alert('Error: Label missing.')
      this.$emit("assign-label", this.axis, segment, label, this.selectedField);
      this.resetSegementLabel();
      this.invalidate();
    },
    resetSegementLabel() {
      this.selectedSegment = null;
      this.selectedSegmentLabel = null;
      this.$emit("highlight-segments", []);
    },
    onSegmentMouseOver(e, segment) {
      this.updateHoverLabels(segment)
      this.$emit("highlight-segments", [segment]);
    },
    updateHoverLabels(segment) {
      if(segment != undefined){
        this.hoverLabel = this.labels[segment] || segment;
        for (let i = 0; i < this.segments.length; i++) {
          if (this.segments[i].segment === segment) {
            this.hoverMin = this.segments[i].min;
            this.hoverMax = this.segments[i].max;
            break;
          }
        } 
      }
    }
  },
};
</script>
