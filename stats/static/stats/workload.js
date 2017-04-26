var get_color_by_expert_slug = function(expert_slug){
    return user_data[expert_slug].color;
};

var cache_data = function(expert_slug,data){
    user_data[expert_slug].data = data;
};


$(function () {
    load_daily_report_input_ajax = function(){
        dailyReportChart.showLoading();
        $.ajax({
            url: '/api/stats/workload_data/report_input/',
            type: "GET",
            dataType: "json",
            success: function(data) {
                dailyReportChart.addSeries({
                    name: 'Number of reports entered the system this day',
                    data: data,
                    color: '#2ca25f',
                    marker: {
                        enabled: false,
                        symbol: 'circle',
                        lineColor: '#000',
                        lineWidth: 1
                    }
                });
                dailyReportChart.hideLoading();
            },
            cache: false
        });
    };

    ajaxload = function(key){
        var checked = $('#' + key).prop('checked');
        if(checked){
            if (user_data[key].data){
                userChart.addSeries({
                    name: user_data[key].name,
                    data: user_data[key].data,
                    color: get_color_by_expert_slug(key),
                    marker: {
                        enabled: false,
                        symbol: 'circle',
                        lineColor: '#000',
                        lineWidth: 0.5
                    }
                });
            }else{
                $('#' + key).attr("disabled", true);
                userChart.showLoading();
                $.ajax({
                    url: '/api/stats/workload_data/user/',
                    type: "GET",
                    dataType: "json",
                    data : {user_slug : key},
                    success: function(data) {
                        $('#' + key).removeAttr("disabled");
                        userChart.hideLoading();
                        userChart.addSeries({
                            name: user_data[key].name,
                            data: data,
                            color: get_color_by_expert_slug(key),
                            marker: {
                                enabled: false,
                                symbol: 'circle',
                                lineColor: '#000',
                                lineWidth: 0.5
                            }
                        });
                        user_data[key].data = data;
                    },
                    cache: false
                });
            }
        }else{
            series = userChart.series;
            for(var i = 0; i < series.length; i++){
                if (series[i].name == user_data[key].name){
                    userChart.series[i].remove();
                }
            }
        }
    };

    get_series_data_from_key = function(key){
        for(var i = 0; i < series_data.length; i++){
            if (series_data[i].name.includes(" - " + key)){
                return series_data[i];
            }
        }
        return null;
    };

    users.forEach(function(key,index){
        $("#userlist").append('<li style="color:' + users[index].color + '" class="list-group-item small-font"><input id="' + users[index].username + '" onclick="javascript:ajaxload(\'' + users[index].username + '\')" type="checkbox">' + users[index].name + '</li>');
    });

    /*
    pendingChart = Highcharts.stockChart('container_pending',{
        chart: {
            type: 'bar'
        },
        title: {
            text: 'Pending reports per expert',
            x: -20 //center
        },
        subtitle: {
            text: null,
            x: -20
        },
        xAxis: {
            categories: ['Pending reports']
            title: {
                text: null
            }
        },
        yAxis: {
            title: {
                text: 'Number of pending reports'
            },
            floor: 0,
            labels: {
                overflow: 'justify'
            }
        },
        legend: {
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'bottom',
            borderWidth: 0
        }
        ,series: null
    });*/

    userChart = Highcharts.stockChart('container',{
        chart: {
            type: 'line'
        },
        title: {
            text: 'Expert Activity',
            x: -20 //center
        },
        rangeSelector: {
            enabled:true
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
                text: 'Number of reports'
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
        }
        ,series: null
    });

    dailyReportChart = Highcharts.stockChart('container_two',{
        chart: {
            type: 'line'
        },
        title: {
            text: 'Daily report input',
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
                text: 'Number of reports'
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
                    name: 'Number of reports entered the system this day',
                    data: report_input_data,
                    color: '#2ca25f',
                    marker: {
                        enabled: false,
                        symbol: 'circle',
                        lineColor: '#000',
                        lineWidth: 1
                    }
                }
            ]
        });
    load_daily_report_input_ajax();
});