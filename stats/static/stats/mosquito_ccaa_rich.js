var data = [];
var data_ccaa = {};
var pre_parsed = {};
var mapData;
var countryChart;
var mapChart;

$(function () {

    for (var i = 0; i < map_data.length; i++){
        var elem = map_data[i];
        if( pre_parsed[elem[3]] == null ){
            pre_parsed[elem[3]] = {};
            for (var j = 0; j < years.length; j++){
                pre_parsed[elem[3]][years[j]] = 0;
            }
        }
        pre_parsed[elem[3]][elem[1]] = elem[0];
        pre_parsed[elem[3]]['name'] = elem[2];
    }

    for (var i = 0; i < map_data.length; i++){
        var elem = map_data[i];
        if( pre_parsed[elem[3]] == null ){
            pre_parsed[elem[3]] = {};
            for (var j = 0; j < years.length; j++){
                pre_parsed[elem[3]][years[j]] = 0;
            }
        }
        pre_parsed[elem[3]][elem[1]] = elem[0];
        pre_parsed[elem[3]]['name'] = elem[2];
    }

    /* Parse data for accumulated, only tiger confirmed */

    for (var key in pre_parsed){
        var sum = 0;
        for (var i = 0; i < years.length; i++){
            sum = sum + pre_parsed[key][years[i]];
        }
        data.push({
            name: pre_parsed[key]['name'],
            cod_ccaa: key,
            value: sum
        });
    }

    for (var key in pre_parsed){
        var year_values = [];
        for (var i = 0; i < years.length; i++){
            year_values.push(pre_parsed[key][years[i]]);
        }
        data_ccaa[key] = {
            name: pre_parsed[key]['name'],
            cod_ccaa: key,
            data: year_values
        }
    }

    var spawn_chart = function(div_id, linechart_id, title_linechart, title, series_title, series_data, cc_aa_data){

        mapData = Highcharts.maps['countries/es/es-all'];
        for (var i = 0; i < mapData.features.length; i++){
            mapData.features[i].properties.id = mapData.features[i].id;
        }

        Highcharts.wrap(Highcharts.Point.prototype, 'select', function (proceed) {

            proceed.apply(this, Array.prototype.slice.call(arguments, 1));

            var points = mapChart.getSelectedPoints();
            if (points.length) {
                $('#info .subheader').html('<h4>' + title_linechart + '</h4><small><em>Shift + Click on map to compare Provinces</em></small>');

                if (!countryChart) {
                    countryChart = Highcharts.chart(linechart_id, {
                        chart: {
                            height: 250,
                            spacingLeft: 0
                        },
                        credits: {
                            enabled: false
                        },
                        title: {
                            text: null
                        },
                        subtitle: {
                            text: null
                        },
                        xAxis: {
                            tickPixelInterval: 50,
                            crosshair: true
                        },
                        yAxis: {
                            title: null,
                            opposite: true
                        },
                        tooltip: {
                            split: true
                        },
                        plotOptions: {
                            series: {
                                animation: {
                                    duration: 500
                                },
                                marker: {
                                    enabled: false
                                },
                                threshold: 0
                                //,pointStart: parseInt(categories[0], 10)
                                ,pointStart: 2014
                            }
                        }
                    });
                }

                $.each(points, function (i) {
                    // Update
                    if (countryChart.series[i]) {
                        countryChart.series[i].update({
                            name: this.name,
                            data: cc_aa_data[this.cod_ccaa].data,
                            type: points.length > 1 ? 'line' : 'area'
                        }, false);
                    } else {
                        countryChart.addSeries({
                            name: this.name,
                            data: cc_aa_data[this.cod_ccaa].data,
                            type: points.length > 1 ? 'line' : 'area'
                        }, false);
                    }
                });
                while (countryChart.series.length > points.length) {
                    countryChart.series[countryChart.series.length - 1].remove(false);
                }
                countryChart.redraw();

            } else {
                $('#info #flag').attr('class', '');
                $('#info h2').html('');
                $('#info .subheader').html('');
                if (countryChart) {
                    countryChart = countryChart.destroy();
                }
            }
        });

        mapChart = Highcharts.mapChart(div_id, {
            title: {
                text: title
            },

            mapNavigation: {
                enabled: true,
                buttonOptions: {
                    verticalAlign: 'bottom'
                }
            },

            colorAxis: {
                type: 'logarithmic',
                /*min: 1,
                max: 1000,*/
                endOnTick: false,
                startOnTick: false,
                minColor: '#fef0d9',
                maxColor: '#b30000'
                //min: 50000
            },

            tooltip: {
                footerFormat: '<span style="font-size: 10px">(Click to see details)</span>'
            },

            series: [{
                data: series_data,
                mapData: mapData,
                joinBy: ['id', 'cod_ccaa'],
                name: series_title,
                allowPointSelect: true,
                cursor: 'pointer',
                states: {
                    select: {
                        color: '#a4edba',
                        borderColor: 'black',
                        dashStyle: 'shortdot'
                    }
                }
            }]
        });
    };

    spawn_chart(
        'container',
        'country-chart',
        title_linechart,
        title,
        series_title,
        data,
        data_ccaa
    );


});

