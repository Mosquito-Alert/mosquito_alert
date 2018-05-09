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
            name: 'Llocs de cria ' + year,
            data: all_data[year].site_series,
            color: site_colors[ year ]
        });
    }
}

var refreshPieSeries = function(){
    var adults_pie_data = [];
    var sites_pie_data = [];
    var checked_years = getCheckedYears();
    removeSeries(chart_adults, 'Informes adults/any');
    removeSeries(chart_sites, 'Informes llocs de cria/any');
    if(checked_years.length > 1){
        for(var i = 0; i < checked_years.length; i++){
            adults_pie_data.push({
                name: 'Adults ' + checked_years[i],
                y: all_data[checked_years[i].toString()].adult_series_pie,
                color: adult_colors[ checked_years[i].toString() ]
            });
            sites_pie_data.push({
                name: 'Llocs de cria ' + checked_years[i],
                y: all_data[checked_years[i].toString()].site_series_pie,
                color: site_colors[ checked_years[i].toString() ]
            });
        }
        chart_adults.addSeries({
            type: 'pie',
            name: 'Informes adults/any',
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
            name: 'Informes llocs de cria/any',
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
        chart_adults = combined_chart_empty("Informes adults", 'base_graph');
    }
    if(chart_sites==null){
        chart_sites = combined_chart_empty("Informes llocs de cria", 'sites');
    }
    var checked = $('#year_check_' + year).prop('checked');
    if(checked){
        addColumnSeries(chart_adults, year);
        addColumnSeries(chart_sites, year);
    }else{
        removeSeries(chart_adults, 'Adults ' + year);
        removeSeries(chart_sites, 'Llocs de cria ' + year);
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
    '2014': '#e6e6ff',
    '2015': '#9999ff',
    '2016': '#6666ff',
    '2017': '#3333ff',
    '2018': '#0000e6'
};

var site_colors = {
    '2014': '#ffcccc',
    '2015': '#ff8080',
    '2016': '#ff6666',
    '2017': '#ff3333',
    '2018': '#e60000'
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
                text: "Nombre d'informes"
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