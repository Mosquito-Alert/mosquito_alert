var all_data = {};
var params_2014;
var params_2015;
var params_2016;
var params_2017;
var params_2018;
var chart_register;

var register_colors = {
    '2014': '#e6ffe6',
    '2015': '#80ff80',
    '2016': '#1aff1a',
    '2017': '#00b300',
    '2018': '#004d00'
}

var extract_series_data = function(year,aggregated_data){
    var series = [];
    for (var i = 0; i < 12; i++){
        series.push(0);
    }
    for(var i = 0; i < aggregated_data.length; i++){
        var data_elem = aggregated_data[i];
        if(data_elem[1]==year){
            series[data_elem[2]-1] = data_elem[0];
        }
    }
    return series;
};

var extract_series_data_pie = function(year, aggregated_data){
    var value = 0;
    for(var i = 0; i < aggregated_data.length; i++){
        var data_elem = aggregated_data[i];
        if(data_elem[1]==year){
            value += data_elem[0]
        }
    }
    return value;
}

var refreshPieSeries = function(){
    var register_pie_data = [];
    var checked_years = getCheckedYears();
    removeSeries(chart_register, 'Usuaris registrats/any');
    if(checked_years.length > 1){
        for(var i = 0; i < checked_years.length; i++){
            register_pie_data.push({
                name: 'Usuaris registrats ' + checked_years[i],
                y: all_data[checked_years[i].toString()].register_series_pie,
                color: register_colors[ checked_years[i].toString() ]
            });
        }
        chart_register.addSeries({
            type: 'pie',
            name: 'Usuaris registrats/any',
            data: register_pie_data,
            center: [200, 80],
            size: 70,
            showInLegend: false,
            dataLabels: {
                enabled: true,
                format: '<b>{point.name}</b>: {y}'
            }
        });
    }
}

var combined_chart_empty = function(title, div_id){
    var chart = Highcharts.chart(div_id, {
        title: {
            text: title
        },
        plotOptions:{
            series:{
                dataLabels:{
                    enabled: true
                }
            }
        },
        xAxis: {
            categories: ['Gener', 'Febrer', 'Març', 'Abril', 'Maig', 'Juny', 'Juliol', 'Agost', 'Setembre', 'Octubre', 'Novembre', 'Desembre']
        },
        yAxis: {
            title: {
                text: "Nombre d'usuaris"
            }
        },
        series: [
        ]
    });
    return chart;
}

var addColumnSeries = function(chart, year){
    if(chart == chart_register){
        chart_register.addSeries({
            type: 'column',
            name: 'Usuaris registrats ' + year,
            data: all_data[year].register_series,
            color: register_colors[ year ]
        });
    }
}

var getCheckedYears = function(){
    var checked_list = [];
    for(var i = 0; i < years_data.length; i++){
        var checked = $('#year_check_' + years_data[i]).prop('checked');
        if(checked){
            checked_list.push(years_data[i]);
        }
    }
    return checked_list;
}

var removeSeries = function(chart, series_name){
    series = chart.series;
    for(var i = 0; i < series.length; i++){
        if (series[i].name == series_name){
            chart.series[i].remove();
        }
    }
}

var addSeries = function(year){
    if(chart_register==null){
        chart_register = combined_chart_empty("Usuaris registrats per mes", 'register');
    }
    var checked = $('#year_check_' + year).prop('checked');
    if(checked){
        addColumnSeries(chart_register, year);
    }else{
        removeSeries(chart_register, 'Usuaris registrats ' + year);
    }
    refreshPieSeries();
}

$(function () {

    years_data.forEach(function(key,index){
        $("#years").append('<li><input id="year_check_' + years_data[index]+ '" onclick="javascript:addSeries(\'' + years_data[index] + '\')" type="checkbox">' + years_data[index] + '</li>');
    });


    for(var i = 0; i < years_data.length; i++){
        all_data[ years_data[i].toString() ] = {
            'register_series': extract_series_data(years_data[i], register_data),
            'register_series_pie': extract_series_data_pie(years_data[i], register_data)
        }
    }

    params_2014 = all_data[ '2014' ];
    params_2015 = all_data[ '2015' ];
    params_2016 = all_data[ '2016' ];
    params_2017 = all_data[ '2017' ];
    params_2018 = all_data[ '2018' ];

});