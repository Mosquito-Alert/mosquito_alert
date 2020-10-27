$(function () {

    var createGaugeChart = function(container,number_of_reports,reports_class,class_short_name){
        Highcharts.chart(container,{
            chart: {
                type: 'solidgauge'
            },
            title: {
                text: reports_class
            },
            pane: {
                center: ['50%', '85%'],
                size: '140%',
                startAngle: -90,
                endAngle: 90,
                background: [
                    {
                        backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
                        innerRadius: '60%',
                        outerRadius: '100%',
                        shape: 'arc'
                    }
                ]
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
                tickAmount: 11,
                title: {
                    y: -70
                },
                labels: {
                    y: 16
                },
                min: 0,
                max: 50
            },
            plotOptions: {
                solidgauge: {
                    dataLabels: {
                        y: 5,
                        borderWidth: 0,
                        useHTML: true
                    }
                }
            },
            series: [{
                    name: reports_class,
                    data: [number_of_reports],
                    dataLabels: {
                        format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                        ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                        '<span style="font-size:12px;color:silver"> ' + class_short_name + '</span></div>'
                    }
                }
            ]
        });
    };


    for(var i = 0; i < data.length; i++){
        createGaugeChart(data[i].ns_country_code + '_unassigned',data[i].unassigned,'Unassigned reports','unassigned');
        createGaugeChart(data[i].ns_country_code + '_progress',data[i].progress,'Reports in progress','progress');
        createGaugeChart(data[i].ns_country_code + '_pending',data[i].pending,'Pending reports','pending');
    }


});