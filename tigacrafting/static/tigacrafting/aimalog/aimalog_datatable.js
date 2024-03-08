var f;
$(document).ready(function () {
    var table = $('#aimalog_table').DataTable({
        'ajax': {
            'url': _aimalog_list_url,
            'dataType': 'json',
            'data': function(d){
                var filter_cookie = getCookie('alerts_f');
                if(filter_cookie){
                    d.filter = filter_cookie;
                }
                //d.filter = $('#filter_value').val();
            }
        },
        "initComplete": function(settings, json) {
            // Bind the event listener to your external filter control
            $('#filter').on('click', function() {
                //$('#filter_value').val(JSON.stringify(f.getJson()));
                f.write_filter_cookie();
                table.draw();
            });
            $('#remove_filter').on('click', function() {
                f.clear();
                //$('#filter_value').val(JSON.stringify(f.getJson()));
                f.write_filter_cookie();
                table.draw();
            });
        },
        'createdRow': function( row, data, dataIndex){
            if( data.comm_status == 0 ){
                $(row).addClass('dtRed');
            }else if ( data.comm_status == 1 ){
                $(row).addClass('dtOrange');
            }else if ( data.comm_status == 2 ){
                $(row).addClass('dtGreen');
            }else{
                $(row).addClass('dtRed');
            }
        },
        'stripeClasses': [],
        'dom': 'lpftrip',
        'stateSave': true,
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
            {'data': 'id'},
            {'data': 'report_id'},
            {'data': 'report_datetime'},
            //{'data': 'loc_code'},
            {'data': 'species'},
            //{'data': 'certainty'},
            {'data': 'status'},
            //{'data': 'hit'},
            {'data': 'review_species'},
            {'data': 'review_status'},
            //{'data': 'review_datetime'},
            {'data': 'country'},
            {'data': 'nuts_one'},
            {'data': 'nuts_two'},
            {'data': 'nuts_three'},
            {'data': 'municipality'},
            //{'data': 'alert_sent'},
            {'data': 'ia_hit'},
            {'data': 'comm_status'},
            {'data': 'validation_status'},
        ],
        'columnDefs': [
            /*{'targets': 0,'title': 'xvb'}*/
            {'targets': 0,'title': 'id'}
            ,{'targets': 1,'title': 'report'}
            ,{'targets': 2,'title': 'report_datetime'}
            /*,{'targets': 3,'title': 'loc_code'}
            ,{'targets': 3, 'title': 'species',}*/
            ,{'targets': 3,'title': 'species'}
            ,{'targets': 4,'title': 'status'}
            /*,{'targets': 7,'title': 'hit',},*/
            ,{'targets': 5,'title': 'review_species'}
            ,{'targets': 6,'title': 'review_status'}
            /*,{'targets': 10,'title': 'review_datetime'}*/
            ,{'targets': 7,'title': 'country'}
            ,{'targets': 8,'title': 'nuts_1'}
            ,{'targets': 9,'title': 'nuts_2'}
            ,{'targets': 10,'title': 'nuts_3'}
            ,{'targets': 11,'title': 'municipality'}
            //,{'targets': 12,'title': 'alert_sent'}
            ,{
                'targets': 12, 'data': null, 'sortable': false, 'title': 'Species match',
                'render': function(value){
                    if(value == true){
                        return '<h4 style="color:red;"><span title="Correct alert" class="glyphicon glyphicon-certificate"></span></h4>';
                    }else if(value == false){
                        return '<h4 style="color:green;"><span title="Incorrect alert" class="glyphicon glyphicon-ban-circle"></span></h4>';
                    }else{
                        return '<h4 style="color:gray;"><span title="Not yet evaluated" class="glyphicon glyphicon glyphicon-question-sign"></span></h4>';
                    }
                }
            }
            ,{
                'targets': 13, 'data': null, 'sortable': false, 'title': 'Comm. status',
                'render': function(value){
                    if(value == 0){
                        return '<h4 style="color:red;"><span title="New" class="glyphicon glyphicon-exclamation-sign"></span></h4>';
                    }else if(value == 1){
                        return '<h4 style="color:orange;"><span title="Accepted" class="glyphicon glyphicon-ok"></span></h4>';
                    }else if(value == 2){
                        return '<h4 style="color:green;"><span title="Accepted and communicated" class="glyphicon glyphicon-envelope"></span></h4>';
                    }else{
                        return '<h4 style="color:red;"><span title="New" class="glyphicon glyphicon-exclamation-sign"></span></h4>';
                    }
                }
            }
            ,{
                'targets': 14, 'data': null, 'sortable': false, 'title': 'Validation complete',
                'render': function(value){
                    if(value == true){
                        return '<h4 style="color:green;"><span title="Complete" class="glyphicon glyphicon-check"></span></h4>';
                    }else{
                        return '<h4 style="color:red;"><span title="Pending" class="glyphicon glyphicon-remove"></span></h4>';
                    }
                }
            }
            ,{
                'targets': 15, 'data': null, 'sortable': false,
                'render': function(value){
                    return '<a title="Process alert" class="review_button btn btn-success" href="/aimalog/process_ui/' + value.report_id + '/' + value.id + '/"><i class="fa fa-pencil-square-o" aria-hidden="true"></i></a>';
                }
            }
        ]
    });

    /*
    var load_municipalities = function(parent_nuts_code, select_id, id_name, name_name, init_select_val){
        $('#' + select_id + "_spinner").show();
        $.ajax({
            url: '/api/municipalities_below/?nuts_from=' + parent_nuts_code,
            type: "GET",
            dataType: "json",
            success: function(data) {
                console.log(data);
                load_data_to_control(select_id,data,id_name,name_name);
                $('#' + select_id + "_spinner").hide();
                if(init_select_val != null){
                    $('#' + select_id).val(init_select_val);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
                $('#' + select_id + "_spinner").hide();
            }
        });
    }

    var load_nuts_level = function(parent_code, select_id, id_name, name_name, init_select_val){
        $('#' + select_id + "_spinner").show();
        $.ajax({
            url: '/api/nuts_below/?nuts_from=' + parent_code,
            type: "GET",
            dataType: "json",
            success: function(data) {
                console.log(data);
                load_data_to_control(select_id, data, id_name, name_name);
                $('#' + select_id + "_spinner").hide();
                if(init_select_val!=null){
                    $('#' + select_id).val(init_select_val);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(textStatus);
                $('#' + select_id + "_spinner").hide();
            }
        });
    }

    var load_data_to_control = function(control_id, data, id_name, name_name){
        $('#' + control_id).empty();
        var in_html = [];
        in_html.push('<option value="">-----</option>');
        for(var i = 0; i < data.length; i++){
            in_html.push('<option value="' + data[i][id_name] + '">' + data[i][name_name] + '</option>');
        }
        $('#' + control_id).html( in_html.join() );
        $('#' + control_id).prop('disabled', false);
    }
    */

    $( "#date_from" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#date_to" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#review_date_from" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#review_date_to" ).datepicker({ dateFormat: 'dd/mm/yy' });

    $('#nuts_0').on('change', function(){
        f.resetAllDropDown();
        f.load_nuts_level($(this).val(), 'nuts_1','nuts_id','name_latn');
    });
    $('#nuts_1').on('change', function(){
        f.load_nuts_level($(this).val(), 'nuts_2','nuts_id','name_latn');
    });
    $('#nuts_2').on('change', function(){
        f.load_nuts_level($(this).val(), 'nuts_3','nuts_id','name_latn');
    });
    $('#nuts_3').on('change', function(){
        f.load_municipalities($(this).val(), 'municipality','natcode','nameunit');
    });

    f = FilterControl.create();

    var filter_cookie = getCookie('alerts_f');
    if(filter_cookie != null && filter_cookie != ''){
        var filter_cookie_j = JSON.parse(filter_cookie);
        f.toJson(filter_cookie_j);
    }
});

$(window).bind('beforeunload', function(){
    f.write_filter_cookie();
});