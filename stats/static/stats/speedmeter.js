$( document ).ready(function() {

    var gaugeOptions = {

        chart: {
            type: 'solidgauge'
        },

        title: null,

        pane: {
            center: ['50%', '85%'],
            size: '140%',
            startAngle: -90,
            endAngle: 90,
            background: {
                backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
                innerRadius: '60%',
                outerRadius: '100%',
                shape: 'arc'
            }
        },

        tooltip: {
            enabled: false
        },

        // the value axis
        yAxis: {
            stops: [
                [0.1, '#55BF3B'], // green
                [0.5, '#DDDF0D'], // yellow
                [0.9, '#DF5353'] // red
            ],
            lineWidth: 0,
            minorTickInterval: null,
            tickAmount: 2,
            title: {
                y: -70
            },
            labels: {
                y: 16
            }
        },

        plotOptions: {
            solidgauge: {
                dataLabels: {
                    y: 5,
                    borderWidth: 0,
                    useHTML: true
                }
            }
        }
    };

    // The speed gauge
    var numberReports = Highcharts.chart('container-number', Highcharts.merge(gaugeOptions, {
        yAxis: {
            min: 0,
            max: 200,
            title: {
                text: 'Number of reports last 7 days'
            }
        },

        credits: {
            enabled: false
        },

        series: [{
            name: 'Speed',
            data: [week_init_value],
            dataLabels: {
                format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                    ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                       '<span style="font-size:12px;color:silver">reports</span></div>'
            },
            tooltip: {
                valueSuffix: ' reports'
            }
        }]

    }));

    var reportFlow = Highcharts.chart('container-flow', Highcharts.merge(gaugeOptions, {
        yAxis: {
            min: 0,
            max: 30,
            title: {
                text: 'Average reports per day, last 7 days'
            }
        },

        series: [{
            name: 'Reports',
            data: [week_init_flow_value],
            dataLabels: {
                format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                    ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y:.1f}</span><br/>' +
                       '<span style="font-size:12px;color:silver">reports</span></div>'
            },
            tooltip: {
                valueSuffix: ' reports'
            }
        }]

    }));

    var load_number_reports_ajax = function(){
        $.ajax({
            url: '/api/stats/speedmeter/',
            type: "GET",
            dataType: "json",
            success: function(data) {
                if (numberReports) {
                    point = numberReports.series[0].points[0];
                    newVal = data.reports_last_seven;
                    if(newVal > 200){
                        newVal = 200;
                    }
                    point.update(newVal);
                }
                if (reportFlow) {
                    point = reportFlow.series[0].points[0];
                    newVal = data.avg_last_seven;
                    if(newVal > 30){
                        newVal = 30;
                    }
                    point.update(newVal);
                }
            },
            cache: false
        });
    };

    setInterval(function () {
        load_number_reports_ajax();
    }, 15000);


});