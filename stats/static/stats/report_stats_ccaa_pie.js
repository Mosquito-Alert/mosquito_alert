var map_parsed_data = [];
var pre_parsed = {};
var chart;
var centers = {};
$(function () {

for( var i = 0; i < map_data.length; i++){
    var elem = map_data[i];
    if (pre_parsed[elem[2]] == null){
        pre_parsed[elem[2]] = {'nom': elem[1], 'mosquito_tiger_confirmed':0,'mosquito_tiger_probable':0,'other_species':0,'unidentified':0,'total': 0};
    }
    pre_parsed[elem[2]][elem[3]] = pre_parsed[elem[2]][elem[3]] + elem[0];
    pre_parsed[elem[2]]['total'] = pre_parsed[elem[2]]['mosquito_tiger_confirmed'] + pre_parsed[elem[2]]['mosquito_tiger_probable'] + pre_parsed[elem[2]]['other_species'] + pre_parsed[elem[2]]['unidentified'];
}

for (var key in pre_parsed){
    _this_row = [key, pre_parsed[key]['nom'], pre_parsed[key]['mosquito_tiger_confirmed'], pre_parsed[key]['mosquito_tiger_probable'], pre_parsed[key]['other_species'],  pre_parsed[key]['unidentified'], pre_parsed[key]['total']];
    map_parsed_data.push(_this_row.slice());
}

var colors = {
    'confirmed': '#e66101',
    'probable': '#fdb863',
    'other': '#5e3c99',
    'noid': '#b2abd2'
};

var mapData = Highcharts.maps['countries/es/es-all'];
for (var i = 0; i < mapData.features.length; i++){
    centers[mapData.features[i].id] = { 'lat': mapData.features[i].properties.latitude, 'long': mapData.features[i].properties.longitude};
}

Highcharts.seriesType('mappie', 'pie', {
    center: null, // Can't be array by default anymore
    clip: true, // For map navigation
    states: {
        hover: {
            halo: {
                size: 5
            }
        }
    },
    dataLabels: {
        enabled: false
    }
},
{
    getCenter: function () {
        var options = this.options,
            chart = this.chart,
            slicingRoom = 2 * (options.slicedOffset || 0);
        if (!options.center) {
            options.center = [null, null]; // Do the default here instead
        }
        // Handle lat/lon support
        if (options.center.lat !== undefined) {
            var point = chart.fromLatLonToPoint(options.center);
            options.center = [
                chart.xAxis[0].toPixels(point.x, true),
                chart.yAxis[0].toPixels(point.y, true)
            ];
        }
        // Handle dynamic size
        if (options.sizeFormatter) {
            options.size = options.sizeFormatter.call(this);
        }
        // Call parent function
        var result = Highcharts.seriesTypes.pie.prototype.getCenter.call(this);
        // Must correct for slicing room to get exact pixel pos
        result[0] -= slicingRoom;
        result[1] -= slicingRoom;
        return result;
    },
    translate: function (p) {
        this.options.center = this.userOptions.center;
        this.center = this.getCenter();
        return Highcharts.seriesTypes.pie.prototype.translate.call(this, p);
    }
});

    var maxTotal = 0;
    Highcharts.each(map_parsed_data, function (row) {
        maxTotal = Math.max(maxTotal, row[5]);
    });

    chart = Highcharts.mapChart('container', {

        title: {
            text: 'Observacions per tipus i comarca'
        },

        subtitle: {
        text: 'Dades acumulades de tots els anys'
        },

        colorAxis: {
            dataClasses: [{
                from: -1,
                to: 0,
                color: colors.confirmed,
                name: 'Mosquit tigre confirmat'
            }, {
                from: 0,
                to: 1,
                color: colors.probable,
                name: 'Mosquit tigre probable'
            }, {
                from: 2,
                to: 3,
                name: 'Altres espècies',
                color: colors.other
            }, {
                from: 3,
                to: 4,
                name: 'No identificable',
                color: colors.noid
            }]
        },

        mapNavigation: {
            enabled: true
        },

        tooltip: {
            useHTML: true
        },

        // Default options for the pies
        plotOptions: {
            mappie: {
                borderColor: 'rgba(255,255,255,0.4)',
                borderWidth: 1,
                tooltip: {
                    headerFormat: ''
                }
            }
        },

        series: [
            {
                mapData: Highcharts.maps['countries/es/es-all'],
                showInLegend: false,
                data: map_parsed_data,
                keys: ['hasc', 'nom', 'mosquito_tiger_confirmed', 'mosquito_tiger_probable', 'other_species', 'unidentified', 'total' ],
                //joinBy: ['hasc','hasc'],
                name: 'Comunitats autònomes',
                states: {
                    hover: {
                        color: '#a4edba'
                    }
                },
                tooltip: {
                    headerFormat: '',
                    pointFormatter: function () {
                        return '<b> Observacions a ' + this.nom + '</b><br/>' +
                            Highcharts.map([
                                ['Mosquit tigre confirmat', this.mosquito_tiger_confirmed, colors.confirmed],
                                ['Mosquit tigre probable', this.mosquito_tiger_probable, colors.probable],
                                ['Altres espècies', this.other_species, colors.other],
                                ['No identificable', this.unidentified, colors.noid]
                            ].sort(function (a, b) {
                                return b[1] - a[1]; // Sort tooltip by most votes
                            }), function (line) {
                                return '<span style="color:' + line[2] +
                                    '">\u25CF</span> ' +
                                    // Party and votes
                                    '<b>' +
                                    line[0] + ': ' +
                                    Highcharts.numberFormat(line[1], 0) +
                                    '</b>' +
                                    '<br/>';
                            }).join('') +
                            '<hr/>Total: ' + Highcharts.numberFormat(this.total, 0);
                    }
                }
            },
            {
                name: 'Separators',
                type: 'mapline',
                data: Highcharts.geojson(Highcharts.maps['countries/es/es-all'], 'mapline'),
                color: '#707070',
                showInLegend: false,
                enableMouseTracking: false
            }
        ]
    });


   Highcharts.each(chart.series[0].points, function (state) {
    if (!state.hasc) {
        return; // Skip points with no data, if any
    }

    if(centers[state.hasc] == null){
        return;
    }

    var pieOffset = state.pieOffset || {},
        centerLat = parseFloat(centers[state.hasc].lat),
        centerLon = parseFloat(centers[state.hasc].long);

    // Add the pie for this state
    chart.addSeries({
            type: 'mappie',
            name: state.hasc,
            zIndex: 6, // Keep pies above connector lines
            sizeFormatter: function () {
                var yAxis = this.chart.yAxis[0],
                    zoomFactor = (yAxis.dataMax - yAxis.dataMin) /
                        (yAxis.max - yAxis.min);
                return Math.max(
                    this.chart.chartWidth / 45 * zoomFactor, // Min size
                    this.chart.chartWidth / 11 * zoomFactor * state.total / maxTotal
                );
            },
            tooltip: {
                // Use the state tooltip for the pies as well
                pointFormatter: function () {
                    return state.series.tooltipOptions.pointFormatter.call({
                        hasc: state.hasc,
                        nom: state.nom,
                        mosquito_tiger_confirmed: state.mosquito_tiger_confirmed,
                        mosquito_tiger_probable: state.mosquito_tiger_probable,
                        other_species: state.other_species,
                        unidentified: state.unidentified,
                        total: state.total
                    });
                }
            },
            data: [{
                name: 'Mosquit tigre confirmat',
                y: state.mosquito_tiger_confirmed,
                color: colors.confirmed
            }, {
                name: 'Mosquit tigre probable',
                y: state.mosquito_tiger_probable,
                color: colors.probable
            }, {
                name: 'Altres espècies',
                y: state.other_species,
                color: colors.other
            }, {
                name: 'No identificable',
                y: state.unidentified,
                color: colors.noid
            }],
            center: {
                lat: centerLat + (pieOffset.lat || 0),
                lon: centerLon + (pieOffset.lon || 0)
            }
        }, false);

        // Draw connector to state center if the pie has been offset
        /*if (pieOffset.drawConnector !== false) {
            var centerPoint = chart.fromLatLonToPoint({
                    lat: centerLat,
                    lon: centerLon
                }),
                offsetPoint = chart.fromLatLonToPoint({
                    lat: centerLat + (pieOffset.lat || 0),
                    lon: centerLon + (pieOffset.lon || 0)
                });
            chart.series[2].addPoint({
                name: state.code_hc,
                path: 'M' + offsetPoint.x + ' ' + offsetPoint.y +
                    'L' + centerPoint.x + ' ' + centerPoint.y
            }, false);
        }*/
    });

chart.redraw();

});