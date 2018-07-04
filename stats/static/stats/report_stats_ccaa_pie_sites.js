var map_parsed_data = [];
var map_parsed_acum = [];
var pre_parsed = {};
var pre_parsed_acum = {};
var centers = {};
var $grid;

var year_map_data = {};

var getCheckedYears = function(){
    var checked_list = [];
    for(var i = 0; i < years_data.length; i++){
        var checked = $('#year_check_' + years_data[i]).prop('checked');
        if(checked){
            checked_list.push(years_data[i]);
        }
    }
    var checked = $('#year_check_acumulat').prop('checked');
    if(checked){
        checked_list.push('acum');
    }
    return checked_list;
}

var showPanel = function(panel_id){

    var checked_years = getCheckedYears();
    var filter_array = [];
    for( var i = 0; i < checked_years.length; i++){
        filter_array.push('#container_' + checked_years[i]);
    }
    filter_string = filter_array.join(',');
    if(filter_string != ''){
        $grid.isotope({ filter: filter_string });
    }else{
        $grid.isotope({ filter: '#kk' });
    }
}

var getIntervalSize = function(max, numIntervals){
    return Math.round(max / numIntervals);
}

var getIntervalNum = function(max, numIntervals, index){
    var retVal = [];
    var intSize = max / numIntervals;
    var lowerBound = index * intSize;
    var upperBound;
    if(index + 1 == numIntervals){
        upperBound = max;
    }else{
        upperBound = lowerBound + intSize;
    }
    retVal.push(lowerBound);
    retVal.push(upperBound);
    return retVal;
}

var getReverseLog = function(value){
    return Math.pow(10,value);
}

$(function () {

    $grid = $('.grid').isotope({
        layoutMode: 'fitRows',
        itemSelector: '.grid-item'
    });
    $grid.isotope({ filter: '#kk' });

    years_data.forEach(function(key,index){
        $("#years").append('<li><input id="year_check_' + years_data[index]+ '" onclick="javascript:showPanel(\'container_' + years_data[index] + '\')" type="checkbox">' + years_data[index] + '</li>');
    });
    $("#years").append('<li><input id="year_check_acumulat" onclick="javascript:showPanel(\'container_acum\')" type="checkbox">All years</li>');

    for( var i = 0; i < map_data.length; i++){
        var elem = map_data[i];
        if (pre_parsed_acum[elem[2]] == null){
            pre_parsed_acum[elem[2]] = {'nom': elem[1], 'storm_drain_water':0,'storm_drain_dry':0,'breeding_site_other':0,'total': 0};
        }
        pre_parsed_acum[elem[2]][elem[3]] = pre_parsed_acum[elem[2]][elem[3]] + elem[0];
        pre_parsed_acum[elem[2]]['total'] = pre_parsed_acum[elem[2]]['storm_drain_water'] + pre_parsed_acum[elem[2]]['storm_drain_dry'] + pre_parsed_acum[elem[2]]['breeding_site_other'];
    }

    for (var key in pre_parsed_acum){
        _this_row = [key, pre_parsed_acum[key]['nom'], pre_parsed_acum[key]['storm_drain_water'], pre_parsed_acum[key]['storm_drain_dry'], pre_parsed_acum[key]['breeding_site_other'],  pre_parsed_acum[key]['total']];
        map_parsed_acum.push(_this_row.slice());
    }

    for( var i = 0; i < map_data_year.length; i++){
        var elem = map_data_year[i];
        if(pre_parsed[elem[1]] == null){
            pre_parsed[elem[1]] = {};
        }
        if (pre_parsed[elem[1]][elem[3]] == null){
            pre_parsed[elem[1]][elem[3]] = {'nom': elem[2], 'storm_drain_water':0,'storm_drain_dry':0,'breeding_site_other':0,'total': 0};
        }
        pre_parsed[elem[1]][elem[3]][elem[4]] = pre_parsed[elem[1]][elem[3]][elem[4]] + elem[0];
        pre_parsed[elem[1]][elem[3]]['total'] = pre_parsed[elem[1]][elem[3]]['storm_drain_water'] + pre_parsed[elem[1]][elem[3]]['storm_drain_dry'] + pre_parsed[elem[1]][elem[3]]['breeding_site_other'];

    }

    for (var year in pre_parsed){
        for (var key in pre_parsed[year]){
            _this_row = [key, pre_parsed[year][key]['nom'], pre_parsed[year][key]['storm_drain_water'], pre_parsed[year][key]['storm_drain_dry'], pre_parsed[year][key]['breeding_site_other'],  pre_parsed[year][key]['total']];
            //map_parsed_data.push(_this_row.slice());
            if( year_map_data[year] == null ){
                year_map_data[year] = [];
            }
            year_map_data[year].push(_this_row.slice());
        }
    }


    var colors = {
        'water': '#0000ff',
        'dry': '#0095ff',
        'other': '#9fdaff'
    };

    var mapData = Highcharts.maps['countries/es/es-all'];
    for (var i = 0; i < mapData.features.length; i++){
        centers[mapData.features[i].id] = { 'lat': mapData.features[i].properties.latitude, 'long': mapData.features[i].properties.longitude};
        mapData.features[i].properties.id = mapData.features[i].id;
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

    var spawn_size_legend = function(div_id, max, interval_1_log, interval_2_log, interval_3_log, interval_4_log){
        var renderer;
        renderer = new Highcharts.Renderer(
            $(div_id)[0],
            600,
            100
        );

        var interval_1 = [ Math.round(getReverseLog(interval_1_log[0])), Math.round(getReverseLog(interval_1_log[1])) ];
        var interval_2 = [ Math.round(getReverseLog(interval_2_log[0])), Math.round(getReverseLog(interval_2_log[1])) ];
        var interval_3 = [ Math.round(getReverseLog(interval_3_log[0])), Math.round(getReverseLog(interval_3_log[1])) ];
        var interval_4 = [ Math.round(getReverseLog(interval_4_log[0])), Math.round(getReverseLog(interval_4_log[1])) ];

        var left_margin = 30;
        var right_margin_1 = 140;
        var right_margin_2 = 240;
        var right_margin_3 = 320;
        var top_margin = 40;
        var bottom_margin = 75;

        var biggest_circle_y = top_margin;
        var biggest_circle_x = left_margin;
        var biggest_circle_radius = 20;

        var bigger_circle_y = top_margin;
        var bigger_circle_x = right_margin_1;
        var bigger_circle_radius = 15;

        var big_circle_y = top_margin;
        var big_circle_x = right_margin_2;
        var big_circle_radius = 10;

        var small_circle_y = top_margin;
        var small_circle_x = right_margin_3;
        var small_circle_radius = 5;

        var right_gap_circle_to_text = 25;
        var top_gap_circle_to_text = 5;

        renderer.text('<strong>Number of observations and pie size</strong>', left_margin - 20, 12 ).attr({
            zIndex: 6
        })
        .css({
            fontSize: '12px',
            fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif'
        })
        .add();

        /* BIGGEST */

        renderer.circle(biggest_circle_x, biggest_circle_y, biggest_circle_radius).attr({
            fill: '#808080',
            'stroke-width': 0,
            zIndex: 5
        })
        .add();

        renderer.text(interval_4[0] + ' to ' + interval_4[1], biggest_circle_x + right_gap_circle_to_text, biggest_circle_y + top_gap_circle_to_text ).attr({
            zIndex: 6
        }).add();

        /* BIGGER */

        renderer.circle(bigger_circle_x, bigger_circle_y, bigger_circle_radius).attr({
            fill: '#808080',
            'stroke-width': 0,
            zIndex: 5
        })
        .add();

        renderer.text(interval_3[0] + ' to ' + interval_3[1], bigger_circle_x + right_gap_circle_to_text, bigger_circle_y + top_gap_circle_to_text ).attr({
            zIndex: 6
        }).add();

        /* BIG */

        renderer.circle(big_circle_x, big_circle_y, big_circle_radius).attr({
            fill: '#808080',
            'stroke-width': 0,
            zIndex: 5
        })
        .add();

        renderer.text( interval_2[0] + ' to ' + interval_2[1] , big_circle_x + right_gap_circle_to_text, big_circle_y + top_gap_circle_to_text ).attr({
            zIndex: 6
        }).add();

        /* SMALL */

        renderer.circle(small_circle_x, small_circle_y, small_circle_radius).attr({
            fill: '#808080',
            'stroke-width': 0,
            zIndex: 5
        })
        .add();

        renderer.text(interval_1[0] + ' to ' + interval_1[1], small_circle_x + right_gap_circle_to_text, small_circle_y + top_gap_circle_to_text ).attr({
            zIndex: 6
        }).add();
    }

    var spawn_chart = function(div_id, map_data, title, subtitle, max, interval_1_log, interval_2_log, interval_3_log, interval_4_log){

        var chart = Highcharts.mapChart(div_id, {

            title: {
                text: title
            },

            /*subtitle: {
            text: subtitle
            },*/

            colorAxis: {
                dataClasses: [{
                    from: -1,
                    to: 0,
                    color: colors.water,
                    name: 'Breeding sites with water'
                }, {
                    from: 0,
                    to: 1,
                    color: colors.dry,
                    name: 'Breeding sites without water'
                }, {
                    from: 2,
                    to: 3,
                    name: 'Other breeding sites',
                    color: colors.other
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
                    data: map_data,
                    keys: ['hasc', 'nom', 'storm_drain_water', 'storm_drain_dry', 'breeding_site_other', 'total' ],
                    //joinBy: ['id','hasc'],
                    name: 'Comunitats autònomes',
                    states: {
                        hover: {
                            color: '#a4edba'
                        }
                    },
                    tooltip: {
                        headerFormat: '',
                        pointFormatter: function () {
                            return '<b> Observations in ' + this.nom + '</b><br/>' +
                                Highcharts.map([
                                    ['Breeding sites with water', this.storm_drain_water, colors.water],
                                    ['Breeding sites without water', this.storm_drain_dry, colors.dry],
                                    ['Other breeding sites', this.breeding_site_other, colors.other]
                                ].sort(function (a, b) {
                                    return b[1] - a[1]; // Sort tooltip by most votes
                                }), function (line) {
                                    return '<span style="color:' + line[2] +
                                        '">\u25CF</span> ' +
                                        // Party and votes
                                        //'<b>' +
                                        line[0] + ': ' +
                                        Highcharts.numberFormat(line[1], 0) +
                                        //'</b>' +
                                        '<br/>';
                                }).join('') +
                                '<hr/>Observations total: ' + Highcharts.numberFormat(this.total, 0);
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
                    /*
                    var yAxis = this.chart.yAxis[0],
                        zoomFactor = (yAxis.dataMax - yAxis.dataMin) / (yAxis.max - yAxis.min);
                    return Math.max(
                        this.chart.chartWidth / 45 * zoomFactor, // Min size
                        this.chart.chartWidth / 11 * zoomFactor * state.total / max
                    );
                    */
                    if (Math.log10(state.total) >= interval_1_log[0] && Math.log10(state.total) < interval_1_log[1]){
                        return 10;
                    } else if ( Math.log10(state.total) >= interval_2_log[0] && Math.log10(state.total) < interval_2_log[1] ){
                        return 20;
                    } else if ( Math.log10(state.total) >= interval_3_log[0] && Math.log10(state.total) < interval_3_log[1] ){
                        return 30;
                    } else {
                        return 40;
                    }

                },
                tooltip: {
                    // Use the state tooltip for the pies as well
                    pointFormatter: function () {
                        return state.series.tooltipOptions.pointFormatter.call({
                            hasc: state.hasc,
                            nom: state.nom,
                            storm_drain_water: state.storm_drain_water,
                            storm_drain_dry: state.storm_drain_dry,
                            breeding_site_other: state.breeding_site_other,
                            total: state.total
                        });
                    }
                },
                data: [{
                    name: 'Breeding sites with water',
                    y: state.storm_drain_water,
                    color: colors.water
                }, {
                    name: 'Breeding sites without water',
                    y: state.storm_drain_dry,
                    color: colors.dry
                }, {
                    name: 'Other breeding sites',
                    y: state.breeding_site_other,
                    color: colors.other
                }],
                center: {
                    lat: centerLat + (pieOffset.lat || 0),
                    lon: centerLon + (pieOffset.lon || 0)
                }
            }, false);
        });

        return chart;
    }

    var max_per_year = {};
    for (var year in year_map_data){
        for ( var measure in year_map_data[year] ){
            if( max_per_year[year]){
                var current_value = max_per_year[year];
                max_per_year[year] = Math.max(current_value, year_map_data[year][measure][5]);
            }else{
                max_per_year[year] = year_map_data[year][measure][5];
            }
        }
    }

    var totalMax = 0;
    for (var year in year_map_data){
        Highcharts.each(year_map_data[year], function (row) {
            totalMax = Math.max(totalMax, row[5]);
        });
    }

    var maxAcum = 0;
    Highcharts.each(map_parsed_acum, function (row) {
        maxAcum = Math.max(maxAcum, row[5]);
    });

    var interval_1_log = getIntervalNum(Math.log10(maxAcum), 4, 0);
    var interval_1 = [ Math.round(getReverseLog(interval_1_log[0])), Math.round(getReverseLog(interval_1_log[1])) ];


    var interval_2_log = getIntervalNum(Math.log10(maxAcum), 4, 1);
    var interval_2 = [ Math.round(getReverseLog(interval_2_log[0])), Math.round(getReverseLog(interval_2_log[1])) ];


    var interval_3_log = getIntervalNum(Math.log10(maxAcum), 4, 2);
    var interval_3 = [ Math.round(getReverseLog(interval_3_log[0])), Math.round(getReverseLog(interval_3_log[1])) ];


    var interval_4_log = getIntervalNum(Math.log10(maxAcum), 4, 3);
    var interval_4 = [ Math.round(getReverseLog(interval_4_log[0])), Math.round(getReverseLog(interval_4_log[1])) ];

    if(year_map_data[2014]){
        //var chart_2014 = spawn_chart('container_2014', year_map_data[2014], 'Year 2014', 'Year 2014', max_per_year[2014]);
        var chart_2014 = spawn_chart('container_2014', year_map_data[2014], 'Year 2014', 'Year 2014', maxAcum, interval_1_log, interval_2_log, interval_3_log, interval_4_log);
        chart_2014.redraw();
    }
    if(year_map_data[2015]){
        //var chart_2015 = spawn_chart('container_2015', year_map_data[2015], 'Year 2015', 'Year 2015', max_per_year[2015]);
        var chart_2015 = spawn_chart('container_2015', year_map_data[2015], 'Year 2015', 'Year 2015', maxAcum, interval_1_log, interval_2_log, interval_3_log, interval_4_log);
        chart_2015.redraw();
    }
    if(year_map_data[2016]){
        //var chart_2016 = spawn_chart('container_2016', year_map_data[2016], 'Year 2016', 'Year 2016', max_per_year[2016]);
        var chart_2016 = spawn_chart('container_2016', year_map_data[2016], 'Year 2016', 'Year 2016', maxAcum, interval_1_log, interval_2_log, interval_3_log, interval_4_log);
        chart_2016.redraw();
    }
    if(year_map_data[2017]){
        //var chart_2017 = spawn_chart('container_2017', year_map_data[2017], 'Year 2017', 'Year 2017', max_per_year[2017]);
        var chart_2017 = spawn_chart('container_2017', year_map_data[2017], 'Year 2017', 'Year 2017', maxAcum, interval_1_log, interval_2_log, interval_3_log, interval_4_log);
        chart_2017.redraw();
    }
    if(year_map_data[2018]){
        //var chart_2018 = spawn_chart('container_2018', year_map_data[2018], 'Year 2018', 'Year 2018', max_per_year[2018]);
        var chart_2018 = spawn_chart('container_2018', year_map_data[2018], 'Year 2018', 'Year 2018', maxAcum, interval_1_log, interval_2_log, interval_3_log, interval_4_log);
        chart_2018.redraw();
    }
    var chart_acum = spawn_chart('container_acum', map_parsed_acum, 'All years', 'Years 2014-2018', maxAcum, interval_1_log, interval_2_log, interval_3_log, interval_4_log);
    chart_acum.redraw();

    spawn_size_legend('#size_legend', maxAcum, interval_1_log, interval_2_log, interval_3_log, interval_4_log);
});