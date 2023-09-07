<template>
  <div class="container-fluid">
    <div class="row">
      <div style="width: 100%;">
        <div class="btn-group" style="float: right;">
          <a class="btn btn-info"
            @click="$store.dispatch('vis/undo')"
            :disabled="overview.segmentationX === null || overview.segmentationY === null">
            undo
          </a>
        </div>
      </div>
    </div>
    <div class="row">
      <div style="width: 33%; min-width: 500px;">
        <segmentation-view-x
          :title="'Segmentation View X'"
          :axis="0"
          v-if="overview.segmentationX.segments"
          :segmentation="overview.segmentationX"
          :selected-segments="overview.selectedSegmentsX"
          :filtered-segments="overview.filteredSegmentsX"
          :highlighted-segments="highlightedSegmentsX"
          :labels="labelsX"
          :treeHeight="overview.treeHeightX"
          :max-watershed-level="overview.maxWatershedLevelX"
          :fieldNames="$store.state.vis.fieldNames"
          :selectedField="overview.selectedFieldX"
          @reset-segment-selection="resetSegmentSelection"
          @add-selected-segment="addSelectedSegment"
          @remove-segment-selection="removeSegmentSelection"
          @assign-label="assignSegmentLabel"
          @highlight-segments="highlightSegmentsX"
          @filter-selection="filterSelection"
          @load-segmentation="loadSegmentation"
          @refine-segments="refineSegments"
          :t="overview.t"
          >
        </segmentation-view-x>
      </div>
      <div style="width: 33%; min-width: 500px;">
        <segmentation-view-y
          :title="'Segmentation View Y'"
          :axis="1"
          v-if="overview.segmentationY.segments"
          :segmentation="overview.segmentationY"
          :selected-segments="overview.selectedSegmentsY"
          :filtered-segments="overview.filteredSegmentsY"
          :highlighted-segments="highlightedSegmentsY"
          :labels="labelsY"
          :treeHeight="overview.treeHeightY"
          :max-watershed-level="overview.maxWatershedLevelY"
          :fieldNames="$store.state.vis.fieldNames"
          :selectedField="overview.selectedFieldY"
          @reset-segment-selection="resetSegmentSelection"
          @add-selected-segment="addSelectedSegment"
          @remove-segment-selection="removeSegmentSelection"
          @assign-label="assignSegmentLabel"
          @highlight-segments="highlightSegmentsY"
          @filter-selection="filterSelection"
          @load-segmentation="loadSegmentation"
          @refine-segments="refineSegments"
          :t="overview.t"
          >
        </segmentation-view-y>
      </div>
      <div style="width: 34%; min-width: 500px;">
        <matrix-view
          ref="matrixView"
          v-if="overview.correlationMatrix.matrix"
          :matrix="overview.correlationMatrix.matrix"
          :dimensions="overview.correlationMatrix.dimensions"
          :highlighted-segments-x="highlightedSegmentsX"
          :highlighted-segments-y="highlightedSegmentsY"
          :selected-segments-x="overview.selectedSegmentsX"
          :selected-segments-y="overview.selectedSegmentsY"
          :linkage="overview.correlationMatrix.linkage"
          :labelsX="labelsX"
          :labelsY="labelsY"
          :t="t"
          @highlight-segments-x="highlightSegmentsX"
          @highlight-segments-y="highlightSegmentsY"
          @set-selected-segments="setSelectedSegments"
          @add-selected-segments="addSelectedSegments"
          @reset-segment-selection="resetSegmentSelection"
          @filter-selection="filterSelection"
          @change-linkage="changeCorrelationMatrixLinkage"
          @change-threshold="changeCorrelationMatrixThreshold"
        >
        </matrix-view>
      </div>
    </div>
    <div class="row">
      <div style="width: 50%; min-width: 500px;">
        <detail-view
          :labelsByFieldName="labelsByFieldName"
          :fieldNames="$store.state.vis.fieldNames"
          :curves="curves"
          @reset-details="resetDetails"
          @load-details="loadDetails"
        ></detail-view>
      </div>
      <div style="width: 50%; min-width: 500px;">
        <image-view
          :mdsImage="overview.mdsImage"
          :fieldNames="$store.state.vis.fieldNames"
          @change-mds-image="changeMDSImage">
        </image-view>
      </div>
    </div>
  </div>
</template>

<script>

import MatrixView from "./MatrixView";
import DetailView from "./DetailView";
import ImageView from "./ImageView";
import SegmentationViewX from "./SegmentationViewAxis.vue";
import SegmentationViewY from "./SegmentationViewAxis.vue";

export default {
  components: { ImageView, DetailView, MatrixView, SegmentationViewX, SegmentationViewY },
  props: {
    overview: { type: Object },
    level: {},
  },
  data() {
    return {
      highlightedSegmentsX: [],
      highlightedSegmentsY: [],
      watershedLevelX: process.env.initWatershedLevel,
      watershedLevelY: process.env.initWatershedLevel,
      t: 0,
      initWatershedLevel: process.env.initWatershedLevel,
    };
  },
  computed: {
    labelsX() {
      return this.overview.labelsX;
    },
    labelsY() {
      return this.overview.labelsY;
    },
    labelsByFieldName() {
      return this.overview.labelsByFieldName;
    },
    hasSelection() {
      return Object.keys(this.overview.selectedSegmentsX).length > 0 || Object.keys(this.overview.selectedSegmentsY).length > 0;
    },
    curves() {
      return this.overview.curves
    },
  },
  mounted() {
    if(Object.keys(this.overview.filteredSegmentsX).length == 0 && Object.keys(this.overview.filteredSegmentsY).length == 0){
      this.loadSegmentation(0, this.initWatershedLevel, null);
      this.loadSegmentation(1, this.initWatershedLevel, null);
    }
    else {
      this.loadSegmentation(0, this.overview.segmentationX.watershed_level, this.overview.segmentationX.name);
      this.loadSegmentation(1, this.overview.segmentationY.watershed_level, this.overview.segmentationY.name);
    }
  },
  methods: {
    resetDetails(){
      this.$store.dispatch("vis/resetDetails", {
        level: this.level,
      });
    },
    loadDetails(){
      this.$store.dispatch("vis/fetchDetails", {
        axis: 0,
        level: this.level,
      });
      this.$store.dispatch("vis/fetchDetails", {
        axis: 1,
        level: this.level,
      });
    },
    resetSegmentSelection(axis) {
      this.$store.dispatch("vis/resetSegmentSelection", {
        axis: axis,
        level: this.level,
      });
    },
    addSelectedSegment(axis, segment) {
      this.$store.dispatch("vis/addSelectedSegment", {
        axis: axis,
        level: this.level,
        segment: segment,
      });
    },
    addSelectedSegments(axis, segments) {
      this.$store.dispatch("vis/addSelectedSegments", {
        axis: axis,
        level: this.level,
        segments: segments,
      });
    },
    removeSegmentSelection(axis, segment) {
      this.$store.dispatch("vis/removeSelectedSegment", {
        axis: axis,
        level: this.level,
        segment: segment,
      });
    },
    assignSegmentLabel(axis, segment, label, fieldName) {
      if (segment === null) return alert("Error: No segment selected.");
      if (label === null || label === "") label = null;
      this.$store.dispatch("vis/assignSegmentLabel", {
        axis: axis,
        level: this.level,
        segment: segment,
        label: label,
        fieldName: fieldName,
      });
      setTimeout(() => {
        this.$forceUpdate();
      }, 1000);
    },
    highlightSegmentsX(segments) {
      if (!segments) segments = [];
      this.highlightedSegmentsX = segments;
    },
    highlightSegmentsY(segments) {
      if (!segments) segments = [];
      this.highlightedSegmentsY = segments;
    },
    setSelectedSegments(axis, segments) {
      this.$store.dispatch("vis/setSelectedSegments", {
        axis: axis,
        level: this.level,
        segments: segments,
      });
    },
    filterSelection() {
      this.$store.dispatch("vis/filterSelection", {
        level: this.level,
      });
    },
    loadSegmentation(axis, watershedLevel, name) {
      if (axis == 0) {
        this.watershedLevelX = watershedLevel
      } else {
        this.watershedLevelY = watershedLevel
      }
      this.$store.dispatch("vis/getTreeHeight", {axis: axis, level: this.level});
      this.$store.dispatch("vis/getMaxWatershedLevel", {axis: axis, level: this.level});
      this.$store
        .dispatch("vis/loadSegmentation", {
          axis: axis,
          level: this.level,
          watershedLevel: watershedLevel,
          name: name,
        })
        .then((response) => {
          if (
            this.overview.segmentationX.watershed_level != undefined &&
            this.overview.segmentationY.watershed_level != undefined
          ) {
            this.loadCorrelationMatrix(
              this.overview.segmentationX.watershed_level,
              this.overview.segmentationY.watershed_level
            );
          }
        });
      this.setSelectedSegments(axis, [])
    },
    loadCorrelationMatrix(watershedLevelX, watershedLevelY) {
      let segmentsX = Object.keys(this.overview.filteredSegmentsX)
      let segmentsY = Object.keys(this.overview.filteredSegmentsY)
      this.$store
        .dispatch("vis/loadCorrelationMatrix", {
          level: this.level,
          watershedLevelX: watershedLevelX,
          watershedLevelY: watershedLevelY,
          segmentsX: segmentsX,
          segmentsY: segmentsY,
        })
        .then((response) => {
          this.t += 1;
        });
    },
    changeCorrelationMatrixLinkage(linkage) {
      this.$store
        .dispatch("vis/changeCorrelationMatrixLinkage", {
          level: this.level,
          linkage: linkage,
        })
        .then((response) => {
          this.loadCorrelationMatrix(
            this.overview.segmentationX.watershed_level,
            this.overview.segmentationY.watershed_level
          );
        });
    },
    changeCorrelationMatrixThreshold(threshold) {
      this.$store
        .dispatch("vis/changeCorrelationMatrixThreshold", {
          level: this.level,
          threshold: threshold,
        })
        .then((response) => {
          this.loadCorrelationMatrix(
            this.overview.segmentationX.watershed_level,
            this.overview.segmentationY.watershed_level
          );
        });
    },
    refineSegments({ axis, segments, watershedLevel }) {
      let watershedLevelX = null
      let watershedLevelY = null
      if(axis == 0){
        watershedLevelX = watershedLevel
        watershedLevelY = this.watershedLevelY
      }
      else{
        watershedLevelX = this.watershedLevelX
        watershedLevelY = watershedLevel
      }
      this.$store
        .dispatch("vis/refineSegments", {
          axis: axis,
          level: this.level,
          segments: segments,
          watershedLevelX: watershedLevelX,
          watershedLevelY: watershedLevelY,
        })
        .then((this.t += 1));
    },
    changeMDSImage(field) {
      this.$store.dispatch("vis/getMdsImage", { level: this.level, selectedField: field });
    },
  },
};
</script>
