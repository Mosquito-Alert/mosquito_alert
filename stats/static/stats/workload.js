var get_color_by_expert_slug = function(expert_slug){
    return user_data[expert_slug].color;
};

var cache_data = function(expert_slug,data){
    user_data[expert_slug].data = data;
};

function jq(myid) {
    return myid.replace( /(:|\.|\[|\]|,|=|@)/g, "\\$1" );
}


$(function () {

    load_available_reports_ajax = function(){
        gaugeChart.showLoading();
        pendingGaugeChart.showLoading();
        overallPendingChart.showLoading();
        var additional_params = "?user_ids=" + user_ids.join(",");
        $.ajax({
            url: '/api/stats/workload_data/available/' + additional_params,
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
                overallPendingChart.addSeries({
                    name: 'Overall pending reports',
                    data: [data['overall_pending']],
                    dataLabels: {
                        format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                        ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                        '<span style="font-size:12px;color:silver"> overall pending</span></div>'
                    }
                });
                gaugeChart.hideLoading();
                pendingGaugeChart.hideLoading();
                overallPendingChart.hideLoading();
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

    pending_report_list = function(key,data){
        var alias_key = key.replace(".","_");
        //$("#pending_detail").append('<li class="list-group-item small-font"><p style="color:white;background-color:' + user_data[key].color + '">' + user_data[key].name + '</p><ul id="pending_r_' + key +'" class="list-inline"></ul></li>');
        $("#pending_detail").append('<li class="list-group-item small-font"><p style="color:white;background-color:' + user_data[key].color + '">' + user_data[key].name + '</p><ul id="pending_r_' + alias_key +'" class="list-inline"></ul></li>');
        for(var i = 0; i < data.current_pending.length; i++){
            $("#pending_r_" + alias_key).append('<li class="list-group-item small-font"><a target="_blank" href="/experts/status/reports/?version_uuid=' + data.current_pending[i].report_id + '">' + data.current_pending[i].report_id + ' - ' + data.current_pending[i].created + '</a></li>')
        }
    };

    load_pending_report_ajax = function(key){
        var checked;
        if(key.includes(".")){
            keyNoDot = jq(key);
            checked = $('#pending_' + keyNoDot).prop('checked');
        }else{
            checked = $('#pending_' + key).prop('checked');
        }


        if(checked){
            if (user_data[key].data_pending){
                pendingChart.addSeries({
                    name: user_data[key].name + ' (' + user_data[key].data_pending.last_activity + ')',
                    data: [user_data[key].data_pending.current_pending_n],
                    color: get_color_by_expert_slug(key),
                    marker: {
                        enabled: false,
                        symbol: 'circle',
                        lineColor: '#000',
                        lineWidth: 1
                    }
                });
            }else{
                $('#pending_' + key).attr("disabled", true);
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
                        $('#pending_' + key).attr("disabled", false);
                        pendingChart.hideLoading();
                        user_data[key].data_pending = data;
                        if(data['current_pending_n'] > 0){
                            pending_report_list(key,data);
                        }
                    },
                    cache: false
                });
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
        var checked;
        if(key.includes(".")){
            keyNoDot = jq(key);
            checked = $('#' + keyNoDot).prop('checked');
        }else{
            checked = $('#' + key).prop('checked');
        }

        //var checked = $('#' + keyNoDot).prop('checked');

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
                if(key.includes(".")){
                    keyNoDot = jq(key);
                    $('#' + keyNoDot).attr("disabled", true);
                }else{
                    $('#' + key).attr("disabled", true);
                }

                userChart.showLoading();

                $.ajax({
                    url: '/api/stats/workload_data/user/',
                    type: "GET",
                    dataType: "json",
                    data : {user_slug : key},
                    success: function(data) {

                        if(key.includes(".")){
                            keyNoDot = jq(key);
                            $('#' + keyNoDot).removeAttr("disabled");
                        }else{
                             $('#' + key).removeAttr("disabled");
                        }
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
        $("#userlist").append('<li style="color:white;background-color:' + users[index].color + '" class="list-group-item small-font"><input id="' + users[index].username + '" onclick="javascript:ajaxload(\'' + users[index].username + '\')" type="checkbox">' + users[index].name + '</li>');
        $("#userlist_pending").append('<li style="color:white;background-color:' + users[index].color + '" class="list-group-item small-font"><input id="pending_' + users[index].username + '" onclick="javascript:load_pending_report_ajax(\'' + users[index].username + '\')" type="checkbox">' + users[index].name + '</li>');
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
            tickAmount: 11,
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
            tickAmount: 11,
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

    overallPendingChart = Highcharts.chart('container_overall_pending',{
        chart: {
            type: 'solidgauge'
        },
        title: {
            text: 'Overall pending reports'
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
    if(load_on_start){
        for(var i = 0; i < users.length; i++){
            var slug = users[i]['username'];
            var escaped_slug = slug.replace('.','\\.');
            $('#'+escaped_slug).click();
            $('#pending_'+escaped_slug).click();
            ajaxload(slug);
            load_pending_report_ajax(slug);
        }
    }
});