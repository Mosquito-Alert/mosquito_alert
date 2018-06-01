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

$(function () {

    $grid = $('.grid').isotope({
        layoutMode: 'fitRows',
        itemSelector: '.grid-item'
    });
    $grid.isotope({ filter: '#kk' });

    years_data.forEach(function(key,index){
        $("#years").append('<li><input id="year_check_' + years_data[index]+ '" onclick="javascript:showPanel(\'container_' + years_data[index] + '\')" type="checkbox">' + years_data[index] + '</li>');
    });
    $("#years").append('<li><input id="year_check_acumulat" onclick="javascript:showPanel(\'container_acum\')" type="checkbox">Dades acumulades tots els anys</li>');

    for( var i = 0; i < map_data.length; i++){
        var elem = map_data[i];
        if (pre_parsed_acum[elem[2]] == null){
            pre_parsed_acum[elem[2]] = {'nom': elem[1], 'mosquito_tiger_confirmed':0,'mosquito_tiger_probable':0,'other_species':0,'unidentified':0,'total': 0};
        }
        pre_parsed_acum[elem[2]][elem[3]] = pre_parsed_acum[elem[2]][elem[3]] + elem[0];
        pre_parsed_acum[elem[2]]['total'] = pre_parsed_acum[elem[2]]['mosquito_tiger_confirmed'] + pre_parsed_acum[elem[2]]['mosquito_tiger_probable'] + pre_parsed_acum[elem[2]]['other_species'] + pre_parsed_acum[elem[2]]['unidentified'];
    }

    for (var key in pre_parsed_acum){
        _this_row = [key, pre_parsed_acum[key]['nom'], pre_parsed_acum[key]['mosquito_tiger_confirmed'], pre_parsed_acum[key]['mosquito_tiger_probable'], pre_parsed_acum[key]['other_species'],  pre_parsed_acum[key]['unidentified'], pre_parsed_acum[key]['total']];
        map_parsed_acum.push(_this_row.slice());
    }

    for( var i = 0; i < map_data_year.length; i++){
        var elem = map_data_year[i];
        if(pre_parsed[elem[1]] == null){
            pre_parsed[elem[1]] = {};
        }
        if (pre_parsed[elem[1]][elem[3]] == null){
            pre_parsed[elem[1]][elem[3]] = {'nom': elem[2], 'mosquito_tiger_confirmed':0,'mosquito_tiger_probable':0,'other_species':0,'unidentified':0,'total': 0};
        }
        pre_parsed[elem[1]][elem[3]][elem[4]] = pre_parsed[elem[1]][elem[3]][elem[4]] + elem[0];
        pre_parsed[elem[1]][elem[3]]['total'] = pre_parsed[elem[1]][elem[3]]['mosquito_tiger_confirmed'] + pre_parsed[elem[1]][elem[3]]['mosquito_tiger_probable'] + pre_parsed[elem[1]][elem[3]]['other_species'] + pre_parsed[elem[1]][elem[3]]['unidentified'];

    }

    for (var year in pre_parsed){
        for (var key in pre_parsed[year]){
            _this_row = [key, pre_parsed[year][key]['nom'], pre_parsed[year][key]['mosquito_tiger_confirmed'], pre_parsed[year][key]['mosquito_tiger_probable'], pre_parsed[year][key]['other_species'],  pre_parsed[year][key]['unidentified'], pre_parsed[year][key]['total']];
            //map_parsed_data.push(_this_row.slice());
            if( year_map_data[year] == null ){
                year_map_data[year] = [];
            }
            year_map_data[year].push(_this_row.slice());
        }
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


    var spawn_chart = function(div_id, map_data, title, subtitle, max){

        var chart = Highcharts.mapChart(div_id, {

            title: {
                text: title
            },

            subtitle: {
            text: subtitle
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
                    data: map_data,
                    keys: ['hasc', 'nom', 'mosquito_tiger_confirmed', 'mosquito_tiger_probable', 'other_species', 'unidentified', 'total' ],
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
                                        //'<b>' +
                                        line[0] + ': ' +
                                        Highcharts.numberFormat(line[1], 0) +
                                        //'</b>' +
                                        '<br/>';
                                }).join('') +
                                '<hr/>Total observacions: ' + Highcharts.numberFormat(this.total, 0);
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
                        this.chart.chartWidth / 11 * zoomFactor * state.total / max
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
        });

        return chart;
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

    if(year_map_data[2014]){
        var chart_2014 = spawn_chart('container_2014', year_map_data[2014], 'Dades any 2014', 'Any 2014', maxAcum);
        chart_2014.redraw();
    }
    if(year_map_data[2015]){
        var chart_2015 = spawn_chart('container_2015', year_map_data[2015], 'Dades any 2015', 'Any 2015', maxAcum);
        chart_2015.redraw();
    }
    if(year_map_data[2016]){
        var chart_2016 = spawn_chart('container_2016', year_map_data[2016], 'Dades any 2016', 'Any 2016', maxAcum);
        chart_2016.redraw();
    }
    if(year_map_data[2017]){
        var chart_2017 = spawn_chart('container_2017', year_map_data[2017], 'Dades any 2017', 'Any 2017', maxAcum);
        chart_2017.redraw();
    }
    if(year_map_data[2018]){
        var chart_2018 = spawn_chart('container_2018', year_map_data[2018], 'Dades any 2018', 'Any 2018', maxAcum);
        chart_2018.redraw();
    }
    var chart_acum = spawn_chart('container_acum', map_parsed_acum, 'Dades acumulades tots els anys', 'Anys 2014-2018', maxAcum);
    chart_acum.redraw();
});