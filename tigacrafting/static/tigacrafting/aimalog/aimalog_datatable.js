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
        'order': [[0, "desc"]],
        'columns': [
            {'data': 'xvb'},
            {'data': 'report_id'},
            {'data': 'report_datetime'},
            {'data': 'loc_code'},
            {'data': 'species'},
            {'data': 'certainty'},
            {'data': 'status'},
            {'data': 'hit'},
            {'data': 'review_species'},
            {'data': 'review_status'},
            {'data': 'review_datetime'},
            {'data': 'country'},
            {'data': 'nuts_one'},
        ],
        'columnDefs': [
            {
                'targets': 0,
                'title': 'xvb'
            },
            {
                'targets': 1,
                'title': 'report'
            },
            {
                'targets': 2,
                'title': 'report_datetime'
            },
            {
                'targets': 3,
                'title': 'loc_code'
            },
            {
                'targets': 4,
                'title': 'species',
            },
            {
                'targets': 5,
                'title': 'certainty',
            },
            {
                'targets': 6,
                'title': 'status',
            },
            {
                'targets': 7,
                'title': 'hit',
            },
            {
                'targets': 8,
                'title': 'review_species',
            },
            {
                'targets': 9,
                'title': 'review_status',
            },
            {
                'targets': 10,
                'title': 'review_datetime',
            },
            {
                'targets': 11,
                'title': 'country',
            },
            {
                'targets': 12,
                'title': 'nuts_1',
            }
        ]
    });

    $( "#date_from" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#date_to" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#review_date_from" ).datepicker({ dateFormat: 'dd/mm/yy' });
    $( "#review_date_to" ).datepicker({ dateFormat: 'dd/mm/yy' });

    f = FilterControl.create();
});