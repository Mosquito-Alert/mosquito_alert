var split_data = {};
var chart_adults;
var chart_sites;

var readableChartNames = {
    'mosquito_tiger_confirmed': 'Confirmed tiger mosquito',
    'mosquito_tiger_probable': 'Possible tiger mosquito',
    'other_species': 'Other species',
    'unidentified': 'Unidentifiable species',
    'storm_drain_dry': 'Storm drain without water',
    'storm_drain_water': 'Storm drain with water',
    'breeding_site_other': 'Other breeding site'
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

var addColumnSeries = function(chart, year){
    var adultSelectValue = $( "#adult_select" ).val();
    var siteSelectValue = $( "#site_select" ).val();
    if(chart == chart_adults){
        chart_adults.addSeries({
            type: 'column',
            name: year,
            //data: all_data[year].adult_series,
            data: extract_series_data(year,split_data[year][adultSelectValue]),
            color: adult_colors[ year ]
        });
    }else if(chart == chart_sites){
        chart_sites.addSeries({
            type: 'column',
            name: year,
            //data: all_data[year].site_series,
            data: extract_series_data(year,split_data[year][siteSelectValue]),
            color: site_colors[ year ]
        });
    }
}

var refreshAdultPieSeries = function(){
    var adults_pie_data = [];
    var checked_years = getCheckedYears();
    removeSeries(chart_adults, 'Adult reports per year');
    var adultSelectValue = $( "#adult_select" ).val();
    if(checked_years.length > 1){
        for(var i = 0; i < checked_years.length; i++){
            adults_pie_data.push({
                name: checked_years[i],
                //y: all_data[checked_years[i].toString()].adult_series_pie,
                y: extract_series_data_pie(checked_years[i],split_data[checked_years[i]][adultSelectValue]),
                color: adult_colors[ checked_years[i].toString() ]
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
    }
}

var refreshSitePieSeries = function(){
    var sites_pie_data = [];
    var checked_years = getCheckedYears();
    removeSeries(chart_sites, 'Breeding site reports per year');
    var siteSelectValue = $( "#site_select" ).val();
    if(checked_years.length > 1){
        for(var i = 0; i < checked_years.length; i++){
            sites_pie_data.push({
                name: checked_years[i],
                //y: all_data[checked_years[i].toString()].site_series_pie,
                y: extract_series_data_pie(checked_years[i],split_data[checked_years[i]][siteSelectValue]),
                color: site_colors[ checked_years[i].toString() ]
            });
        }
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

var refreshPieSeries = function(){
    refreshAdultPieSeries();
    refreshSitePieSeries();
}

var addAdultSeries = function(year){
    var adultSelectValue = $( "#adult_select" ).val();

    if(chart_adults==null){
        chart_adults = combined_chart_empty("Adult reports", 'base_graph');
    }

    chart_adults.setTitle({text: readableChartNames[adultSelectValue]});

    var checked = $('#year_check_' + year).prop('checked');
    if(checked){
        addColumnSeries(chart_adults, year);
    }else{
        removeSeries(chart_adults, year);
    }
    //refreshPieSeries();
    refreshAdultPieSeries();
}

var addSiteSeries = function(year){
    var siteSelectValue = $( "#site_select" ).val();

    if(chart_sites==null){
        chart_sites = combined_chart_empty("Breeding site reports", 'sites');
    }

    chart_sites.setTitle({text: readableChartNames[siteSelectValue]});

    var checked = $('#year_check_' + year).prop('checked');
    if(checked){
        addColumnSeries(chart_sites, year);
    }else{
        removeSeries(chart_sites, year);
    }
    //refreshPieSeries();
    refreshSitePieSeries();
}

var addSeries = function(year){
    addAdultSeries(year);
    addSiteSeries(year);
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

    $( "#adult_select" ).change(function() {
        var adultSelectValue = $(this).val();
        var years = getCheckedYears();

        if(chart_adults){
            while(chart_adults.series.length > 0){
                chart_adults.series[0].remove(true);
            }

            for( var i = 0; i < years.length; i++){
                addAdultSeries(years[i]);
            }
        }
    });

    $( "#site_select" ).change(function() {
        var siteSelectValue = $(this).val();
        var years = getCheckedYears();

        if(chart_sites){
            while(chart_sites.series.length > 0){
                chart_sites.series[0].remove(true);
            }

            for( var i = 0; i < years.length; i++){
                addSiteSeries(years[i]);
            }
        }
    });

    for(var i = 0; i < years_data.length; i++){
        split_data[years_data[i].toString()] = {};
        split_data[years_data[i].toString()]['mosquito_tiger_confirmed'] = [];
        split_data[years_data[i].toString()]['mosquito_tiger_probable'] = [];
        split_data[years_data[i].toString()]['other_species'] = [];
        split_data[years_data[i].toString()]['unidentified'] = [];
        split_data[years_data[i].toString()]['storm_drain_dry'] = [];
        split_data[years_data[i].toString()]['storm_drain_water'] = [];
        split_data[years_data[i].toString()]['breeding_site_other'] = [];
        for(var j = 0; j < all_sliced_data.length; j++){
            var elem = all_sliced_data[j];
            if(elem[1] === years_data[i]){
                split_data[years_data[i].toString()][elem[3]].push([elem[0],elem[1],elem[2]])
            }
        }
    }

});