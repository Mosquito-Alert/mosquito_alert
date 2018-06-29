var all_data = {};
var params_2014;
var params_2015;
var params_2016;
var params_2017;
var params_2018;
var chart_adults;
var chart_sites;

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

var addColumnSeries = function(chart, year){
    if(chart == chart_adults){
        chart_adults.addSeries({
            type: 'column',
            name: 'Adults ' + year,
            data: all_data[year].adult_series,
            color: adult_colors[ year ]
        });
    }else if(chart == chart_sites){
        chart_sites.addSeries({
            type: 'column',
            name: 'Breeding sites ' + year,
            data: all_data[year].site_series,
            color: site_colors[ year ]
        });
    }
}

var refreshPieSeries = function(){
    var adults_pie_data = [];
    var sites_pie_data = [];
    var checked_years = getCheckedYears();
    removeSeries(chart_adults, 'Adult reports per year');
    removeSeries(chart_sites, 'Breeding site reports per year');
    if(checked_years.length > 1){
        for(var i = 0; i < checked_years.length; i++){
            adults_pie_data.push({
                name: 'Adults ' + checked_years[i],
                y: all_data[checked_years[i].toString()].adult_series_pie,
                color: adult_colors[ checked_years[i].toString() ]
            });
            sites_pie_data.push({
                name: 'Breeding sites ' + checked_years[i],
                y: all_data[checked_years[i].toString()].site_series_pie,
                color: site_colors[ checked_years[i].toString() ]
            });
        }
        chart_adults.addSeries({
            type: 'pie',
            name: 'Adult reports per year',
            data: adults_pie_data,
            center: [200, 80],
            size: 70,
            showInLegend: false,
            dataLabels: {
                enabled: true,
                format: '<b>{point.name}</b>: {y}'
            }
        });
        chart_sites.addSeries({
            type: 'pie',
            name: 'Breeding site reports per year',
            data: sites_pie_data,
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


var addSeries = function(year){
    if(chart_adults==null){
        chart_adults = combined_chart_empty("Adult reports", 'base_graph');
    }
    if(chart_sites==null){
        chart_sites = combined_chart_empty("Breeding site reports", 'sites');
    }
    var checked = $('#year_check_' + year).prop('checked');
    if(checked){
        addColumnSeries(chart_adults, year);
        addColumnSeries(chart_sites, year);
    }else{
        removeSeries(chart_adults, 'Adults ' + year);
        removeSeries(chart_sites, 'Breeding sites ' + year);
    }
    refreshPieSeries();
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

var adult_colors = {
    '2014': '#fef0d9',
    '2015': '#fdcc8a',
    '2016': '#fc8d59',
    '2017': '#e34a33',
    '2018': '#b30000'
};


var site_colors = {
    '2014': '#f1eef6',
    '2015': '#bdc9e1',
    '2016': '#74a9cf',
    '2017': '#2b8cbe',
    '2018': '#045a8d'
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
            categories: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'Desember']
        },
        yAxis: {
            title: {
                text: "Number of reports"
            }
        },
        series: [
        ]
    });
    return chart;
}

$(function () {

    years_data.forEach(function(key,index){
        $("#years").append('<li><input id="year_check_' + years_data[index]+ '" onclick="javascript:addSeries(\'' + years_data[index] + '\')" type="checkbox">' + years_data[index] + '</li>');
    });


    for(var i = 0; i < years_data.length; i++){
        all_data[ years_data[i].toString() ] = {
            'adult_series': extract_series_data(years_data[i], adults_data),
            'site_series': extract_series_data(years_data[i], sites_data),
            'adult_series_pie': extract_series_data_pie(years_data[i], adults_data),
            'site_series_pie': extract_series_data_pie(years_data[i], sites_data)
        }
    }

    params_2014 = all_data[ '2014' ];
    params_2015 = all_data[ '2015' ];
    params_2016 = all_data[ '2016' ];
    params_2017 = all_data[ '2017' ];
    params_2018 = all_data[ '2018' ];

});