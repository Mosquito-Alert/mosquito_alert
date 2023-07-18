$(document).ready(function () {
    var table = $('#aimalog_table').DataTable({
        'ajax': {
            'url': _aimalog_list_url,
            'dataType': 'json',
            'data': function(d){
                d.teststring = 'kk';
            }
        },
        'serverSide': true,
        'processing': true,
        'language': 'en',
        'pageLength': 25,
        'pagingType': 'full_numbers',
        'bLengthChange': false, //allow changing number of entries per page
        'responsive': true,
        'order': [[0, "desc"]],
        'columns': [
            {'data': 'xvb'},
            {'data': 'report'},
            {'data': 'report_datetime'},
            {'data': 'locCode'},
            {'data': 'species'},
            {'data': 'certainty'},
            {'data': 'status'},
            {'data': 'hit'},
            {'data': 'review_species'},
            {'data': 'review_status'},
            {'data': 'review_datetime'}
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
                'title': 'locCode'
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
            }
        ]
    });
});