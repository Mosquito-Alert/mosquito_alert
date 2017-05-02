var get_color_by_expert_slug = function(expert_slug){
    return user_data[expert_slug].color;
};

var cache_data = function(expert_slug,data){
    user_data[expert_slug].data = data;
};


$(function () {

    load_available_reports_ajax = function(){
        gaugeChart.showLoading();
        pendingGaugeChart.showLoading();
        $.ajax({
            url: '/api/stats/workload_data/available/',
            type: "GET",
            dataType: "json",
            success: function(data) {
                gaugeChart.addSeries({
                    name: 'Pending reports',
                    data: [data['current_pending_n']],
                    dataLabels: {
                        format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                        ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                        '<span style="font-size:12px;color:silver"> unassigned</span></div>'
                    }
                });
                pendingGaugeChart.addSeries({
                    name: 'In progress reports',
                    data: [data['current_progress_n']],
                    dataLabels: {
                        format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                        ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                        '<span style="font-size:12px;color:silver"> in progress</span></div>'
                    }
                });
                gaugeChart.hideLoading();
                pendingGaugeChart.hideLoading();
            },
            cache: false
        });
    };

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

    load_pending_report_ajax = function(key){
        var checked = $('#pending_' + key).prop('checked');
        if(checked){
            if (user_data[key].data_pending){
                pendingChart.addSeries({
                    name: user_data[key].name,
                    data: user_data[key].data_pending,
                    color: get_color_by_expert_slug(key),
                    marker: {
                        enabled: false,
                        symbol: 'circle',
                        lineColor: '#000',
                        lineWidth: 1
                    }
                });
            }else{
                pendingChart.showLoading();
                $.ajax({
                    url: '/api/stats/workload_data/pending/',
                    type: "GET",
                    dataType: "json",
                    data : {user_slug : key},
                    success: function(data) {
                        pendingChart.addSeries({
                            name: user_data[key].name + ' (' + data['last_activity'] + ')',
                            data: [data['current_pending_n']],
                            color: get_color_by_expert_slug(key),
                            marker: {
                                enabled: false,
                                symbol: 'circle',
                                lineColor: '#000',
                                lineWidth: 1
                            }
                        });
                        pendingChart.hideLoading();
                    },
                    cache: false
                });
                user_data[key].data_pending = data;
            }
        }else{
            series = pendingChart.series;
            for(var i = 0; i < series.length; i++){
                if (series[i].name.includes(user_data[key].name)){
                    pendingChart.series[i].remove();
                }
            }
        }
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
        $("#userlist_pending").append('<li style="color:' + users[index].color + '" class="list-group-item small-font"><input id="pending_' + users[index].username + '" onclick="javascript:load_pending_report_ajax(\'' + users[index].username + '\')" type="checkbox">' + users[index].name + '</li>');
    });

    pendingGaugeChart = Highcharts.chart('pending_gauge',{
        chart: {
            type: 'solidgauge'
        },
        title: {
            text: 'Reports in progress'
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
            tickAmount: 9,
            title: {
                y: -70
            },
            labels: {
                y: 16
            },
            min: 0,
            max: 100
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
        series: null
    });

    gaugeChart = Highcharts.chart('container_gauge',{
        chart: {
            type: 'solidgauge'
        },
        title: {
            text: 'Unassigned reports'
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
                /*,{
                    backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
                    innerRadius: '20%',
                    outerRadius: '59%',
                    shape: 'arc'
                }*/
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
            tickAmount: 9,
            title: {
                y: -70
            },
            labels: {
                y: 16
            },
            min: 0,
            max: 100
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
        series: null
                /*[
                    {
                        name: 'Unclaimed reports',
                        data: [80],
                        dataLabels: {
                            format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                            ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                            '<span style="font-size:12px;color:silver"> available reports</span></div>'
                        }
                    },
                    {
                        name: 'Some reports',
                        data: [60],
                        dataLabels: {
                            format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                            ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                            '<span style="font-size:12px;color:silver"> available reports</span></div>'
                        }
                    }
                ]*/
    });

    pendingChart = Highcharts.chart('container_pending',{
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
            categories: ['Pending reports'],
            title: {
                text: null
            }
        },
        yAxis: {
            allowDecimals: false,
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
        },
        series: null
    });

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
    load_available_reports_ajax();
});