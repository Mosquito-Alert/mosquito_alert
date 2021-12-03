var myChart;
$(document).ready(function() {

    /*
    Highcharts.chart('activity_all', {
        chart: {
            type: 'bar'
        },
        title: {
            text: 'Number of reports by expert'
        },
        subtitle: {
            text: 'Anonymized data'
        },
        xAxis: {
            categories: activity_data_series,
            title: {
                text: null
            }
        },
        yAxis: {
            min: 0,
            title: {
                text: 'Number of validated reports',
                align: 'high'
            },
            labels: {
                overflow: 'justify'
            }
        },
        plotOptions: {
            bar: {
                dataLabels: {
                    enabled: true
                }
            },
            scales:{
                xAxes: [{
                    ticks: {
                        display: false //this will remove only the label
                    }
                }]
            }
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'top',
            x: -40,
            y: 80,
            floating: true,
            borderWidth: 1,
            backgroundColor:
                Highcharts.defaultOptions.legend.backgroundColor || '#FFFFFF',
            shadow: true
        },
        credits: {
            enabled: false
        },
        series: [{
            name: 'N of completed reports',
            data: activity_data_values
        }]
    });
    */
    var ctx = document.getElementById('activity_all').getContext('2d');
    myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: activity_data_series,
            datasets: [{
                label: 'Number of completed reports',
                data: activity_data_values,
                backgroundColor: color_series,
                borderColor: [
                    'rgba(0, 0, 0, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                },
                x: {
                    display: false //this will remove only the label
                }
            }
        }
    });

});