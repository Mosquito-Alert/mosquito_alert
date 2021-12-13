var myChart;
var accuracy_hard_chart;
var accuracy_soft_chart;
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
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                },
                x: {
                    display: false //this will remove only the label
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return "";
                        }
                    }
                }
            }
        }
    });

    ctx = document.getElementById('accuracy_hard').getContext('2d');
    accuracy_hard_chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: accuracy_hard_series,
            datasets: [{
                label: 'Hard (complete coincidence) accuracy (%)',
                data: accuracy_hard_values,
                backgroundColor: color_series_accuracy_hard,
                borderColor: [
                    'rgba(0, 0, 0, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                },
                x: {
                    display: false //this will remove only the label
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return "";
                        }
                    }
                }
            }
        }
    });

    ctx = document.getElementById('accuracy_soft').getContext('2d');
    accuracy_soft_chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: accuracy_soft_series,
            datasets: [{
                label: 'Soft (partial coincidence) accuracy (%)',
                data: accuracy_soft_values,
                backgroundColor: color_series_accuracy_soft,
                borderColor: [
                    'rgba(0, 0, 0, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                },
                x: {
                    display: false //this will remove only the label
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return "";
                        }
                    }
                }
            }
        }
    });

    expertProgressChart = Highcharts.stockChart('container_two',{
        chart: {
            type: 'line'
        },
        title: {
            text: 'Accuracy progression over time',
            x: -20 //center
        },
        subtitle: {
            text: null,
            x: -20
        },
        xAxis: {
            type: 'datetime',
            dateTimeLabelFormats: {
            day: '%d/%m/%y'
        }
        },
        yAxis: {
            title: {
                text: 'Accuracy (%)'
            },
            floor: 0,
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080'
            }]
        },
        tooltip: {
            dateTimeLabelFormats:{
                minute: '%d/%m/%y, %H:%M'
            }
        },
        legend: {
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'bottom',
            borderWidth: 0
        },
        series:
            [
                {
                    name: 'Hard Accuracy (%)',
                    data: hard_progress_data,
                    color: '#DF5353',
                    marker: {
                        enabled: false,
                        symbol: 'circle',
                        lineColor: '#000',
                        lineWidth: 1
                    }
                }
            ]
        });

});