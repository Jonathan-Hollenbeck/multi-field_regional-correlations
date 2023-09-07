<template>
  <div class="card" style="user-select: none;">
    <h5 class="card-header">Similarity Image
      <span class="float-right"><small><a @click="show = !show"><span v-if="show">hide</span><span
              v-else>show</span></a></small></span>
    </h5>
    <div class="card-body" v-show="show">
      <select class="form-control" v-model="selectedField" @change="$emit('change-mds-image', selectedField)">
        <option v-for="field in fieldNames">{{ field }}</option>
      </select>
      <!--      <label><input type="checkbox" v-model="swap"> Swap half width</label> -->
      <label v-if="$store.state.vis.overlay"><input type="checkbox" v-model="showOverlay"> Show overlay</label>
      <div style="position: relative">
        <img :src="'data:image/png;base64,' + mdsImage" style="width: 100%"
          :style="isRotated ? 'transform: rotate(180deg) scaleX(-1)' : null">
        <img :src="'data:image/png;base64,' + $store.state.vis.overlay"
          style="width: 100%; position: absolute; height: 103.5%; left:0.25% ; top: -2%; right: 0"
          :style="!isRotated ? 'transform:rotate(180deg) scaleX(-1)' : null" v-if="showOverlay">
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props:{
    mdsImage: { required: true },
    fieldNames: { type: Array, required: true }
  },
  components: {},
  computed: {
    isRotated() {
      return process.env.isRotated
    },
    swap: {
      get() { return this.$store.state.vis.swapHalf },
      set(swapHalf) { this.$store.dispatch('vis/swapHalf', swapHalf) }
    }
  },
  watch: {
    fieldNames() {
      this.selectedField = this.fieldNames[0];
    }
  },
  data() {
    return {
      showOverlay: false,
      show: true,
      selectedField: null
    }
  },
  created() {
  },
  mounted() {
      this.selectedField = this.fieldNames[0];
      this.$emit('change-mds-image', this.selectedField)
  },
  methods: {
  }
}
</script>
