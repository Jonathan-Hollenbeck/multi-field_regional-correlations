<template>
  <div class="card" style="user-select: none;">
    <h5 class="card-header"><a style="color: inherit; text-decoration: none;" @click="loadDetails">Statistics <small>(load)</small></a>
      <span><a class="btn btn-secondary btn-sm" @click="resetDetails">Reset data</a></span>
      <span class="float-right"><small><a @click="show = !show">
      <span v-if="show">hide</span>
      <span v-else>show</span></a></small></span>
    </h5>
    <div class="card-body" v-show="show">
      <div ref="detailWrapper" id="detailWrapper"></div>
    </div>
    <div class="card-footer">
      <div class="row">
        <div class="col-sm-6">
          <label><input type="checkbox" v-model="yearly" @change="invalidate"> Show yearly x-axis ticks </label><br>
          <label><input type="checkbox" v-model="drawCurves" @change="redrawGraph"> draw as curves </label><br>
          <label><input type="checkbox" v-model="drawTooltip" @change="redrawGraph"> Show tooltip </label>
        </div>
        <div class="col-sm-3">
          <input v-model="xLabel" class="form-control" placeholder="x label">
        </div>
        <div class="col-sm-3">
          <input v-model="fontsize" class="form-control" placeholder="fontsize">
        </div>
      </div>
    </div>
    <div class="card-footer" v-show="show">
    </div>
  </div>
</template>

<script>
import * as d3 from "d3";

export default {
  components: {
  },
  props: {
    labelsByFieldName: {},
    fieldNames: { type: Array, required: true },
    curves: {},
  },
  data() {
    return {
      show: true,
      scale: 'linear',
      yearly: false,
      drawCurves: false,
      drawTooltip: false,
      xLabel: 'timestep',
      yLabel: 'value',
      fontsize: 10,
      dataset: [],
      ctx: null,
      canvas: null,
      cardMarginLeft: 21,
      width: 0,
      height: 0,
      margin: { top: 10, bottom: 40, left: 70, right: 10},
      yAxisMargin: 70,
      pathLabelRectSize: {width: 20, height: 10},
      zoomTickSpeed: 0.1,
      x_domain: [0, 0],
      is_panning: false,
      pan_last_x: 0
    }
  },
  computed: {
  },
  watch: {
    curves: {
      deep: true,
      handler(){
        this.invalidate()
      }
    }
  },
  created() {
  },
  mounted() {
    window.addEventListener("resize", this.invalidate);
    this.invalidate()
  },
  methods: {
    loadDetails(){
      this.$emit('load-details')
      this.invalidate()
    },
    resetDetails(){
      this.$emit('reset-details')
      this.invalidate()
    },
    invalidate() {
      setTimeout(() => {
        this.width = this.$refs.detailWrapper.clientWidth - this.margin.left - this.margin.right
        this.height = (this.$refs.detailWrapper.clientWidth / 2) - this.margin.top - this.margin.bottom

        this.drawGraph()
      }, 1)
    },
    drawGraph() {
      d3.select("#detailWrapper").selectAll('*').remove()
      //load data
      this.dataset = this.getData();

      //only continue if dataset is not empty
      if(this.dataset.length > 0){
        if(this.yearly == true){
          for (let field of this.dataset){
            for (let curve of field.curves) {
              for(let datum of curve.data){
                datum.time /= 12
              }
            }
          }
        }
        this.x_domain = d3.extent(this.dataset[0].curves[0].data, d => d.time)

        this.redrawGraph()
      }
    },
    redrawGraph(){
      if(this.dataset.length == 0) {
        return;
      }
      //remove all current content, to redraw
      d3.select(this.$refs.detailWrapper).selectAll('*').remove()

      //setup graph
      const svg = d3.select(this.$refs.detailWrapper)
        .append("svg")
          .attr("width", this.width + this.margin.left + this.margin.right)
          .attr("height", this.height + this.margin.top + this.margin.bottom)
          .on("mousedown", this.onMouseDown)
          .on("mouseup", this.onMouseUp)
          .on('mousemove', this.onMouseMove)
          .on('mouseleave', this.onMouseUp)
          .on("wheel", this.onMouseWheel)
        .append("g")
          .attr("transform", 'translate(' + String(this.margin.left) + ', ' + String(this.margin.top) + ')')

      //labels on top
      const path_labels = svg.append("g")

      //offsets for positioning
      let path_rows = 1
      let current_labels_width = 0
      let labels_space = 5
      let median_label_width = this.getTextWidth(" median")
      let upper_label_width = this.getTextWidth(" upper")
      let lower_label_width = this.getTextWidth(" lower")
      const vue_this = this

      //loop through curves
      for (let field of this.dataset){
        for (let curve of field.curves) {
          //text width for positioning
          let label_width = this.getTextWidth(curve.label)
          let complete_label_width = label_width + median_label_width + upper_label_width + lower_label_width
          //line break when out of room on the right
          if(this.margin.left + current_labels_width + complete_label_width > this.width){
            current_labels_width = 0
            path_rows++
          }

          //group for labels
          const label = path_labels.append("g")
            .attr("transform", 'translate(' + current_labels_width + ', ' + ((this.pathLabelRectSize.height * 1.5) * (path_rows - 1)) + ')')
          //create color rectangles
          label.append("svg:rect")
            .attr("width", this.pathLabelRectSize.width)
            .attr("height", this.pathLabelRectSize.height)
            .attr("x", "0")
            .attr("y", "0")
            .attr("fill", curve.color)

          //create label text
          label.append("text")
            .attr("x", this.pathLabelRectSize.width + 5)
            .attr("y", this.pathLabelRectSize.height - 2)
            .style("text-anchor", "left")
            .style("font-size", this.pathLabelRectSize.height + "px")
            .style("fill", "#000000")
            .style("font-family", "sans-serif")
            .text(curve.label)

          //text_decoration depending on visibility of median
          let median_text_decoration = curve.median_visibility == "visible" ? "none" : "line-through"
          //median label
          label.append("text")
            .attr("id", "label_" + String(curve.label) + "_median")
            .attr("x", this.pathLabelRectSize.width + 5 + label_width)
            .attr("y", this.pathLabelRectSize.height - 2)
            .style("text-anchor", "left")
            .style("font-size", this.pathLabelRectSize.height + "px")
            .style("fill", "#000000")
            .style("font-family", "sans-serif")
            .style("text-decoration", median_text_decoration)
            .text(" median")
            .on("click", function() {vue_this.onLabelClick(curve.label, "median")})

          //text_decoration depending on visibility of upper bound
          let upper_text_decoration = curve.upper_visibility == "visible" ? "none" : "line-through"
          //upper label
          label.append("text")
            .attr("id", "label_" + String(curve.label) + "_upper")
            .attr("x", this.pathLabelRectSize.width + 5 + label_width + median_label_width)
            .attr("y", this.pathLabelRectSize.height - 2)
            .style("text-anchor", "left")
            .style("font-size", this.pathLabelRectSize.height + "px")
            .style("fill", "#000000")
            .style("font-family", "sans-serif")
            .style("text-decoration", upper_text_decoration)
            .text(" upper")
            .on("click", function() {vue_this.onLabelClick(curve.label, "upper")})

          //text_decoration depending on visibility of median
          let lower_text_decoration = curve.lower_visibility == "visible" ? "none" : "line-through"
          //lower label
          label.append("text")
            .attr("id", "label_" + String(curve.label) + "_lower")
            .attr("x", this.pathLabelRectSize.width + 5 + label_width + median_label_width + upper_label_width)
            .attr("y", this.pathLabelRectSize.height - 2)
            .style("text-anchor", "left")
            .style("font-size", this.pathLabelRectSize.height + "px")
            .style("fill", "#000000")
            .style("font-family", "sans-serif")
            .style("text-decoration", lower_text_decoration)
            .text(" lower")
            .on("click", function() {vue_this.onLabelClick(curve.label, "lower")})
          
          current_labels_width += this.pathLabelRectSize.width + complete_label_width + labels_space
        }
      }

      const graph = svg.append("g")
        .attr("transform", 'translate(0, ' + String(this.pathLabelRectSize.height * 1.5 * path_rows) + ')')

      const graph_width = this.width
      const graph_height = this.height - (this.pathLabelRectSize.height * 1.5 * path_rows)
      
      //clippath, so the lines of the graph dont lap over the axis
      graph.append("defs").append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
        .attr("width", graph_width - (this.yAxisMargin * (this.dataset.length - 1)))
        .attr("height", graph_height)
        .attr("x", this.yAxisMargin * (this.dataset.length - 1))
        .attr("y", 0)

      //set size of graph
      const x = d3.scaleLinear()
        .range([this.yAxisMargin * (this.dataset.length - 1), graph_width])
      const y = d3.scaleLinear()
        .range([graph_height, 0])

      //set x domain
      x.domain(this.x_domain)

      //x Axis
      graph.append("g")
        .attr("transform", 'translate(0, ' + String(graph_height) + ')')
        .style("font-size", String(this.fontsize) + "px")
        .call(d3.axisBottom(x))

      //x Axis label
      graph.append("text")
        .attr("transform", 'translate(0, ' + String(graph_height - 10) + ')')
        .attr("x", graph_width / 2)
        .attr("y", this.margin.bottom)
        .style("text-anchor", "middle")
        .style("font-size", this.fontsize + "px")
        .style("fill", "#000000")
        .style("font-family", "sans-serif")
        .text(this.xLabel)

      //vertical Gridlines
      graph.append("g").selectAll("xGrid")
        .data(x.ticks().slice(0))
        .join("line")
        .attr("x1", d => x(d))
        .attr("y1", 0)
        .attr("x2", d => x(d))
        .attr("y2", graph_height)
        .attr("stroke", "#e0e0e0")
        .attr("stroke-width", 0.5)
        .attr("clip-path", "url(#clip)")
      
      for (let i = 0; i < this.dataset.length; i++){
        let field = this.dataset[i]
        //set y domain
        y.domain(this.getMinMaxForYAxis(field.curves))

        //y Axis
        graph.append("g")
          .style("font-size", String(this.fontsize) + "px")
          .call(d3.axisLeft(y))
          .attr("transform", 'translate(' + (this.yAxisMargin * i) + ', 0)')

        //y Axis label
        graph.append("text")
          .attr("transform", "translate(" + ((this.yAxisMargin * i) - this.yAxisMargin + this.cardMarginLeft) + ", " + graph_height / 2 + "), rotate(-90)")
          .style("text-anchor", "middle")
          .style("font-size", this.fontsize + "px")
          .style("fill", "#000000")
          .style("font-family", "sans-serif")
          .text(this.getFieldIDToLetter(field.id) + "_" + this.fieldNames[field.id])

        //horizontal Gridlines
        graph.append("g").selectAll("yGrid")
          .data(y.ticks().slice(0))
          .join("line")
          .attr("x1", 0)
          .attr("y1", d => y(d))
          .attr("x2", graph_width)
          .attr("y2", d => y(d))
          .attr("stroke", "#e0e0e0")
          .attr("stroke-width", 0.5)
          .attr("clip-path", "url(#clip)")

        let curveType = this.drawCurves == true ? d3.curveMonotoneX : d3.curveLinear

        //draw lines and areas      
        //create line creater for median lines
        const line_median = d3.line().curve(curveType)
          .x(d => x(d.time))
          .y(d => y(d.median))

        //create are generator for upper area
        const area_lower = d3.area().curve(curveType)
          .x(d => x(d.time))
          .y0(d => y(d.median))
          .y1(d => y(d.lower))

        //create are generator for upper area
        const area_upper = d3.area().curve(d3.curveLinear).curve(curveType)
          .x(d => x(d.time))
          .y0(d => y(d.median))
          .y1(d => y(d.upper))

        for (let curve of field.curves) {
          if(curve.median_visibility == "visible"){
            //median line
            graph.append("g").append("path")
              .datum(curve.data)
              .attr("fill", "none")
              .attr("stroke", curve.color)
              .attr("stroke-width", 2)
              .attr("stroke-dasharray", '10,' + String(i * 2))
              .attr("d", line_median)
              .attr("clip-path", "url(#clip)")
              .attr("id", "path_" + String(curve.label))
          }
          if(curve.upper_visibility == "visible"){
            //upper bound area
            graph.append("g").append("path")
              .datum(curve.data)
              .attr("d", area_upper)
              .style("fill", curve.color)
              .style("fill-opacity", 0.5)
              .attr("clip-path", "url(#clip)")
              .attr("id", "path_" + String(curve.label))
          }
          if(curve.lower_visibility == "visible"){
            //lower bound area
            graph.append("g").append("path")
              .datum(curve.data)
              .attr("d", area_lower)
              .style("fill", curve.color)
              .style("fill-opacity", 0.5)
              .attr("clip-path", "url(#clip)")
              .attr("id", "path_" + String(curve.label))
          }
        }
      }

      //tooltip
      const tooltip = d3.select(this.$refs.detailWrapper)
        .append("div")
          .attr("class", "tooltip")
          .style("position", "absolute")
          .style("padding", "10px")
          .style("background-color", "white")
          .style("color", "black")
          .style("border", "1px solid black")
          .style("border-radius", "10px")
          .style("display", "none")
          .style("opacity", ".75")

      //tooltip point
      const circle = graph.append("circle")
        .attr("r", 0)
        .attr("opacity", .70)

      //listening rect for tooltip via mouse position
      graph.append("rect")
        .attr("width", graph_width - (this.yAxisMargin * (this.dataset.length - 1)))
        .attr("height", graph_height)
        .attr("x", this.yAxisMargin * (this.dataset.length - 1))
        .style("pointer-events", "all")
        .style("fill-opacity", "0")
        .style("stroke-opacity", "0")
        .on("mousemove", function (event){
          if(vue_this.drawTooltip == true){
            let mouse_pos = d3.pointer(event, this)
            const bisectTime = d3.bisector(d => d.time).left
            let x0 = x.invert(mouse_pos[0])
            let i = bisectTime(vue_this.dataset[0].curves[0].data, x0, 1)
            let curve_time = x0 - i + 0.5 >= 0 ? i : i - 1
            let xPos = vue_this.yearly == true ? x(curve_time / 12) : x(curve_time)

            let yPos = 0
            let curve_median = 0
            let curve_width = 0
            let curve_label = ""
            let current_relative_distance = Number.MAX_VALUE
            let circle_color = "rgba(255,0,0,1)"
            for(let field of vue_this.dataset){
              let field_min_max = vue_this.getMinMaxForYAxis(field.curves)
              for(let curve of field.curves) {
                if(curve.median_visibility == "visible"){
                  let curve_value = curve.data[curve_time].median
                  //scale curve value to current y domain
                  let curve_value_scaled = (((curve_value - field_min_max[0]) * (y.domain()[1] - y.domain()[0])) / (field_min_max[1] - field_min_max[0])) + y.domain()[0]
                  let y0 = y.invert(mouse_pos[1])
                  //relative distance between scaled curve median and mouse pos in y domain
                  let distance = Math.pow(curve_value_scaled - y0, 2)
                  if(distance < current_relative_distance){
                    current_relative_distance = distance
                    yPos = y(curve_value_scaled)
                    curve_median = curve_value
                    circle_color = curve.color
                    curve_width = curve.data[curve_time].width
                    curve_label = curve.label
                  }
                }
              }
            }

            circle
              .attr("cx", xPos)
              .attr("cy", yPos)
              .attr("r", 5)
              .attr("fill", circle_color)

            tooltip
              .style("display", "block")
              .style("left", `${xPos + 100}px`)
              .style("top",`${yPos + 50}px`)
              .html("segment: " + curve_label + "</br> timestep: " + curve_time + "</br> median: " + curve_median.toFixed(4) + "</br> width: " + curve_width.toFixed(4))
          }
        })
        .on("mouseleave", function(){
          circle.transition()
            .attr("r", 0)
          
          tooltip.style("display", "none")
        })
    },
    getTextWidth(text) {
      let container = d3.select('body').append('svg');
      container.append('text')
        .attr("x", "-1000")
        .attr("y", "-1000")
        .style("font-size", this.pathLabelRectSize.height + "px")
        .style("font-family", "sans-serif")
        .text(text);
      let size = container.node().getBBox();
      container.remove();
      return size.width;
    },
    getMinMaxForYAxis(curves){
      let min = Number.MAX_VALUE
      let max = Number.MIN_VALUE
      for(let curve of curves){
        let temp_min = 0
        if(curve.lower_visibility == "visible"){
          temp_min = d3.min(curve.data, d => d.lower)
          min = temp_min < min ? temp_min : min
        }
        else if(curve.median_visibility == "visible"){
          temp_min = d3.min(curve.data, d => d.median)
          min = temp_min < min ? temp_min : min
        }

        let temp_max = 0
        if(curve.upper_visibility == "visible"){
          temp_max = d3.max(curve.data, d => d.upper)
          max = temp_max > max ? temp_max : max
        }
        else if(curve.median_visibility == "visible"){
          temp_max = d3.max(curve.data, d => d.median)
          max = temp_max > max ? temp_max : max
        }
      }
      return [min, max]
    },
    onLabelClick(label, type){
      for (let field of this.dataset){
        for (let curve of field.curves) {
          if (label == curve.label){
            if(type == "median"){
              if (curve.median_visibility == "visible"){
                curve.median_visibility = "hidden"
              } else {
                curve.median_visibility = "visible"
              }
            }
            else if(type == "upper"){
              if (curve.upper_visibility == "visible"){
                curve.upper_visibility = "hidden"
              } else {
                curve.upper_visibility = "visible"
              }
            }
            else if(type == "lower"){
              if (curve.lower_visibility == "visible"){
                curve.lower_visibility = "hidden"
              } else {
                curve.lower_visibility = "visible"
              }
            }
            break;
          }
        }
      }
      this.redrawGraph()
    },
    onMouseDown(event) {
      const card_dist_left = 21
      let m_x_graph_pos = event.layerX - this.margin.left - card_dist_left
      if(m_x_graph_pos > 0 && m_x_graph_pos <= this.width){
        this.pan_last_x = event.layerX
        this.is_panning = true
      }
    },
    onMouseUp(event) {
      this.is_panning = this.is_panning == true ? false : false
    },
    onMouseMove(event) {
      let min_max = d3.extent(this.dataset[0].curves[0].data, d => d.time)
      if(this.is_panning == true){
        let m_x = event.layerX

        let pan_dist = ((this.x_domain[1] - this.x_domain[0]) / (this.width - (this.margin.left * (this.dataset.length - 1)))) * (this.pan_last_x - m_x)
        this.pan_last_x = m_x

        let new_left = this.x_domain[0] + pan_dist
        let new_right = this.x_domain[1] + pan_dist

        //check for min max
        if(new_left > min_max[0] && new_right < min_max[1]){
          this.x_domain = [new_left, new_right]
          this.redrawGraph()
        }
      }
    },
    onMouseWheel(event) {
      let current_x_domain_range = this.x_domain[1] - this.x_domain[0]
      let min_max = d3.extent(this.dataset[0].curves[0].data, d => d.time)
      let m_x_graph_pos = event.layerX - this.margin.left - this.cardMarginLeft
      if(m_x_graph_pos > 0 && m_x_graph_pos <= this.width && (current_x_domain_range >= 1 || event.deltaY > 0)){
        let m_x_pos_percentage_from_left = m_x_graph_pos / this.width

        let zoomTickSpeed = current_x_domain_range * this.zoomTickSpeed

        let zoom_left = zoomTickSpeed * m_x_pos_percentage_from_left
        let zoom_right = zoomTickSpeed * (1 - m_x_pos_percentage_from_left)

        let new_left = event.deltaY > 0 ? this.x_domain[0] - zoom_left : this.x_domain[0] + zoom_left
        let new_right = event.deltaY > 0 ? this.x_domain[1] + zoom_right : this.x_domain[1] - zoom_right

        //check for min max
        new_left = new_left < min_max[0] ? min_max[0] : new_left
        new_right = new_right > min_max[1] ? min_max[1] : new_right

        //check for reverse zoom
        if(new_left < new_right && new_right > new_left){
          this.x_domain = [new_left, new_right]
          this.redrawGraph()
        }
      }
    },
    getData() {
      let data = []
      for (let fieldID in this.curves){
        let fieldData = {id: fieldID, curves: []}
        for (let segment in this.curves[fieldID]) {
          let all_curves = this.curves[fieldID][segment]
          let label = this.getPathLabel(fieldID, segment)

          let median = JSON.parse(JSON.stringify(all_curves['median']))
          let lower = JSON.parse(JSON.stringify(all_curves['lower_bound']))
          let upper = JSON.parse(JSON.stringify(all_curves['upper_bound']))
          let width = JSON.parse(JSON.stringify(all_curves['width']))

          let color = `rgba(${all_curves.color[0]}, ${all_curves.color[1]}, ${all_curves.color[2]})`

          let curve = {label: label, color: color, median_visibility: "visible", upper_visibility: "hidden", lower_visibility: "hidden", data: []}
          for (let i = 0; i < median.length; i++){
            curve.data.push({time: i, median: median[i], upper: upper[i], lower: lower[i], width: width[i]})
          }
          fieldData.curves.push(curve)
        }
        data.push(fieldData)
      }
      return data
    },
    getFieldIDToLetter(fieldID){
      return String.fromCharCode(Number(fieldID) + 65)
    },
    getPathLabel(fieldID, segment){
      let fieldName = this.fieldNames[fieldID]
      let label = segment
      if (this.labelsByFieldName[fieldName] != undefined && this.labelsByFieldName[fieldName][segment] != undefined) {
        label = this.labelsByFieldName[fieldName][segment]
      }
      return this.getFieldIDToLetter(fieldID) + '_' + label
    },
  }
}
</script>
