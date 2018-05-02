$(function () {


    var cc_aa_dict = {};

    for(var i = 0; i < data_ccaa.length; i++){
        var row = data_ccaa[i];
        cc_aa_dict[row[0]]=row[1];
    }

    var data_adults = {}
    var data_sites = {}
    var data_acumulat_adults = {}
    var data_acumulat_sites = {}

    for(var i = 0; i < reports_data.length; i++){

        var row = reports_data[i];
        var year = row[1];

        var single_ca_data = [];
        single_ca_data.push(row[0]);
        single_ca_data.push(row[3]);

        if(row[2]=='adult'){

            if (data_adults[year] == null){
                data_adults[year] = []
            }
            data_adults[year].push(single_ca_data);

            if (data_acumulat_adults[row[0]] == null){
                data_acumulat_adults[row[0]] = row[3];
            }else{
                data_acumulat_adults[row[0]] = data_acumulat_adults[row[0]] + row[3];
            }

        }else{
            if (data_sites[year] == null){
                data_sites[year] = []
            }
            data_sites[year].push(single_ca_data);

            if (data_acumulat_sites[row[0]] == null){
                data_acumulat_sites[row[0]] = row[3];
            }else{
                data_acumulat_sites[row[0]] = data_acumulat_sites[row[0]] + row[3];
            }
        }
    }

    var create_summary = function(data, title, ul_id){
        $('#' + ul_id).empty();
        var r_title = '<tr><th> __title__ </th></tr>';
        r_title = r_title.replace('__title__',title);
        $('#' + ul_id).append(r_title);
        for (var i = data.length - 1; i >= 0; i--){
            var data_bit = data[i];
            var tr = '<tr><td> __comunitat__ </td><td>&nbsp;<td><td> __num__ </td></tr>';
            tr = tr.replace('__comunitat__', cc_aa_dict[data_bit[0]]);
            tr = tr.replace('__num__',data_bit[1]);
            $('#' + ul_id).append(tr);
        }
    }


    var spawn_chart = function(title, series_title, series_data, div_id, min_color, max_color){
        Highcharts.mapChart(div_id, {
        chart: {
            map: geojson
        },

        title: {
            text: title
        },

        mapNavigation: {
            enabled: true,
            buttonOptions: {
                verticalAlign: 'top'
            }
        },

        colorAxis: {
            //type: 'logarithmic',
            tickPixelInterval: 50,
            minColor: min_color,
            maxColor: max_color
        },

        legend: {
            layout: 'vertical',
            borderWidth: 0,
            backgroundColor: 'rgba(255,255,255,0.85)',
            floating: false,
            align: 'right',
            verticalAlign: 'middle',
            y: 25
        },

        series: [
            {
                data: series_data,
                keys: ['cod_ccaa', 'value'],
                joinBy: 'cod_ccaa',
                name: series_title,
                states: {
                    hover: {
                        color: '#a4edba'
                    }
                },
                dataLabels: {
                    enabled: true,
                    format: '{point.properties.nom_ccaa} - {point.value}'
                },
                tooltip: {
                    pointFormat: '{point.properties.nom_ccaa}: {point.value}'
                }
            }
        ]
        });
    };

    var graph_data_adults = {};
    var graph_data_sites = {};

    for (var key in data_adults){
        graph_data_adults[key] = data_adults[key].slice();
    }

    for (var key in data_sites){
        graph_data_sites[key] = data_sites[key].slice();
    }

    var graph_data_acum_adults = [];
    for (var key in data_acumulat_adults){
        var data_bit = [];
        data_bit.push(key);
        data_bit.push(data_acumulat_adults[key]);
        graph_data_acum_adults.push(data_bit);
    }
    var presorted_acum_adults = graph_data_acum_adults.slice();

    var graph_data_acum_sites = [];
    for (var key in data_acumulat_sites){
        var data_bit = [];
        data_bit.push(key);
        data_bit.push(data_acumulat_sites[key]);
        graph_data_acum_sites.push(data_bit);
    }
    var presorted_acum_sites = graph_data_acum_sites.slice();


    for(var i = 0; i < year_list.length; i++){
        var year = year_list[i].toString();
        spawn_chart('Densitat de mostreig Adults/Comunitat autònoma - ' + year, 'Número de reports - ' + year, graph_data_adults[year], year,'#FFEEEE','#EE0000');
        spawn_chart('Densitat de mostreig Llocs de cria/Comunitat autònoma - ' + year, 'Número de reports - ' + year, graph_data_sites[year], year + "_s",'#FFEEEE','#0000FF');
        var sorted_data_adults = _.sortBy(data_adults[year], function(elem){ return elem[1]; })
        create_summary(sorted_data_adults, "Nombre de reports adults per Comunitat, " + year, year + "_a_l");
        var sorted_data_sites = _.sortBy(data_sites[year], function(elem){ return elem[1]; })
        create_summary(sorted_data_sites, "Nombre de reports llocs de cria per Comunitat, " + year, year + "_s_l");
    }

    spawn_chart('Densitat de mostreig Adults/Comunitat autònoma acumulat', 'Número de reports', graph_data_acum_adults, 'acum_a','#FFEEEE','#EE0000');
    var sorted_data_adults_acum = _.sortBy(presorted_acum_adults, function(elem){ return elem[1]; })
    create_summary(sorted_data_adults_acum, "Nombre de reports adults per Comunitat acumulats", "acum_a_l");

    spawn_chart('Densitat de mostreig Llocs de cria/Comunitat autònoma acumulat', 'Número de reports', graph_data_acum_sites, 'acum_s','#FFEEEE','#0000FF');
    var sorted_data_sites_acum = _.sortBy(presorted_acum_sites, function(elem){ return elem[1]; })
    create_summary(sorted_data_sites_acum, "Nombre de reports adults per Comunitat acumulats", "acum_s_l");

    /*console.log(graph_data_adults);
    console.log(data_adults);*/



});