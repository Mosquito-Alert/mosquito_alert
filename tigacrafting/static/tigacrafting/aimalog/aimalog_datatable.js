var f;
$(document).ready(function () {
    var table = $('#aimalog_table').DataTable({
        'ajax': {
            'url': _aimalog_list_url,
            'dataType': 'json',
            'data': function(d){
                d.filter = $('#filter_value').val();
            }
        },
        "initComplete": function(settings, json) {
            // Bind the event listener to your external filter control
            $('#filter').on('click', function() {
                $('#filter_value').val(JSON.stringify(f.getJson()));
                table.draw();
            });
            $('#remove_filter').on('click', function() {
                f.clear();
                $('#filter_value').val(JSON.stringify(f.getJson()));
                table.draw();
            });
        },
        'dom': 'lpftrip',
        'serverSide': true,
        'processing': true,
        'language': 'en',
        'pageLength': 100,
        'pagingType': 'full_numbers',
        'bLengthChange': false, //allow changing number of entries per page
        'responsive': true,
        'order': [[2, "desc"]],
        'columns': [
            //{'data': 'xvb'},
            {'data': 'report_id'},
            {'data': 'report_datetime'},
            //{'data': 'loc_code'},
            {'data': 'species'},
            {'data': 'certainty'},
            {'data': 'status'},
            //{'data': 'hit'},
            {'data': 'review_species'},
            {'data': 'review_status'},
            //{'data': 'review_datetime'},
            {'data': 'country'},
            {'data': 'nuts_one'},
            {'data': 'nuts_two'},
            {'data': 'nuts_three'},
            {'data': 'alert_sent'},
        ],
        'columnDefs': [
            /*{
                'targets': 0,
                'title': 'xvb'
            },*/
            {
                'targets': 0,
                'title': 'report'
            },
            {
                'targets': 1,
                'title': 'report_datetime'
            },
            /*{
                'targets': 3,
                'title': 'loc_code'
            },*/
            {
                'targets': 2,
                'title': 'species',
            },
            {
                'targets': 3,
                'title': 'certainty',
            },
            {
                'targets': 4,
                'title': 'status',
            },
            /*{
                'targets': 7,
                'title': 'hit',
            },*/
            {
                'targets': 5,
                'title': 'review_species',
            },
            {
                'targets': 6,
                'title': 'review_status',
            },
            /*{
                'targets': 10,
                'title': 'review_datetime',
            },*/
            {
                'targets': 7,
                'title': 'country',
            },
            {
                'targets': 8,
                'title': 'nuts_1',
            }
            ,
            {
                'targets': 9,
                'title': 'nuts_2',
            }
            ,
            {
                'targets': 10,
                'title': 'nuts_3',
            }
            ,
            {
                'targets': 11,
                'title': 'alert_sent',
            }
        ]
    });

    var load_nuts_level = function(parent_code, select_id){
        $('#' + select_id + "_spinner").show();
        $.ajax({
            url: '/api/nuts_below/?nuts_from=' + parent_code,
            type: "GET",
            dataType: "json",
            success: function(data) {
                console.log(data);
                load_data_to_control(select_id,data);
                $('#' + select_id + "_spinner").hide();
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
                $('#' + select_id + "_spinner").hide();
            }
        });
    }

    var load_data_to_control = function(control_id, data){
        $('#' + control_id).empty();
        var in_html = [];
        in_html.push('<option value="">-----</option>');
        for(var i = 0; i < data.length; i++){
            in_html.push('<option value="' + data[i].nuts_id + '">' + data[i].name_latn + '</option>');
        }
        $('#' + control_id).html( in_html.join() );
        $('#' + control_id).prop('disabled', false);
    }

    $( "#date_from" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#date_to" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#review_date_from" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#review_date_to" ).datepicker({ dateFormat: 'dd/mm/yy' });

    $('#nuts_0').on('change', function(){
        f.resetAllDropDown();
        load_nuts_level($(this).val(), 'nuts_1');
    });
    $('#nuts_1').on('change', function(){
        load_nuts_level($(this).val(), 'nuts_2');
    });
    $('#nuts_2').on('change', function(){
        load_nuts_level($(this).val(), 'nuts_3');
    });

    f = FilterControl.create();
});