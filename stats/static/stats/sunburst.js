var cc_aa = [];
var prov = [];
var muni = [];
var processed_data = [];

$( document ).ready(function() {

    for(var i = 0; i < data.length; i++){
        var elem = data[i];
        var candidate_cc_aa = {
            'id':elem[2],
            'name':elem[1],
            'parent':'0'
        };
        var candidate_prov = {
            'id':elem[4],
            'name':elem[3],
            'parent':elem[2]
        };
        var candidate_muni = {
            'id':elem[6],
            'name':elem[5],
            'parent':elem[4]
        };
        if( _.find(cc_aa, function(o){ return o.id == candidate_cc_aa.id }) == null ){
            cc_aa.push(candidate_cc_aa);
        }
        if( _.find(prov, function(o){ return o.id == candidate_prov.id }) == null ){
            prov.push(candidate_prov);
        }
        var existing_muni;
        if( (existing_muni = _.find(muni, function(o){ return o.id == candidate_muni.id })) == null ){
            candidate_muni.value = 1;
            muni.push(candidate_muni);
        }else{
            existing_muni.value = existing_muni.value + 1;
        }
    }

    processed_data.push({'id':'0','name':'Spain','parent':''});

    processed_data = processed_data.concat(cc_aa, prov, muni);

    console.log(processed_data);

    Highcharts.getOptions().colors.splice(0, 0, 'transparent');


    Highcharts.chart('container', {

        chart: {
            height: '1000px'
        },

        title: {
            text: graph_title
        },
        series: [{
            type: "sunburst",
            data: processed_data,
            allowDrillToNode: true,
            cursor: 'pointer',
            dataLabels: {
                format: '{point.name}',
                filter: {
                    property: 'innerArcLength',
                    operator: '>',
                    value: 16
                }
            },
            levels: [{
                level: 1,
                levelIsConstant: false,
                dataLabels: {
                    filter: {
                        property: 'outerArcLength',
                        operator: '>',
                        value: 64
                    }
                }
            }, {
                level: 2,
                colorByPoint: true
            },
            {
                level: 3,
                colorVariation: {
                    key: 'brightness',
                    to: -0.5
                }
            }, {
                level: 4,
                colorVariation: {
                    key: 'brightness',
                    to: 0.5
                }
            }]

        }],
        tooltip: {
            headerFormat: "",
            pointFormat: 'The number of observations in <b>{point.name}</b> is <b>{point.value}</b>'
        }
    });

});