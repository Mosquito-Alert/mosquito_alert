var create_graph = function(id){
    margin = {right: 0, left: 10}
    width = 200;

    var vis = d3.select("#" + id).append("svg");
    var w = width;
    var h = 10;
    vis.attr("width", w).attr("height", h);

    var lg = vis.append("defs").append("linearGradient")
    .attr("id", "mygrad")//id of the gradient
    .attr("x1", "0%")
    .attr("x2", "100%")
    .attr("y1", "0%")
    .attr("y2", "0%");

    lg.append("stop")
    .attr("offset", "0%")
    .style("stop-color", "red")//end in red
    .style("stop-opacity", 1);

    lg.append("stop")
    .attr("offset", "100%")
    .style("stop-color", "lightgreen")
    .style("stop-opacity", 1);

    var rectangle = vis.append("rect")
    .attr("x", 0 + margin.left)
    .attr("y", 0)
    .attr("width", width - margin.right - margin.left)
    .attr("height", 10)
    .style("fill", "url(#mygrad)");

    var scale = d3.scaleLinear()
        .domain([-1, 1])
        .range([margin.left, width - margin.right]);

    var x_axis = d3.axisBottom()
        .scale(scale)
        .ticks(4);

    vis.append("g")
        .attr("transform", "translate(0,10)")
        .call(x_axis);

    var ia_value = $('#' + id).data('ia-value');
    var dom_value = scale(ia_value);

    var nodes = [ {x:dom_value, y:5} ]
    vis.selectAll("circle .nodes")
    .data(nodes)
    .enter()
    .append("svg:circle")
    .attr("class", "nodes")
    .attr("cx", function(d) { return d.x; })
    .attr("cy", function(d) { return d.y; })
    .attr("r", "4px")
    .attr("fill", "white")
};

$(document).ready(function() {
    $('.ia_graph').each(function(){
        //console.log($(this).attr('id'));
        try{
            create_graph( $(this).attr('id') );
        }catch(error){
            console.log(error);
        }
    });

});