$(document).ready(function () {
    var table = $('#notifications_table').DataTable({
        'ajax': {
            'url': _group_list_url,
            'dataType': 'json'
        },
        'language': 'en',
        'pageLength': 25,
        searchHighlight: true, // not working :(
        'pagingType': 'full_numbers',
        'bLengthChange': true, //allow changing number of entries per page
        'responsive': true,
        'order': [[0, "desc"]],
        'columns': [
            { 'data': 'date_comment' },
            { 'data': 'notification_content.title_en' },
            { 'data': 'notification_content.title_native' },
            { 'data': 'sent_to' },
            { 'data': 'link' },
        ],
        'columnDefs': [
            {
                'targets': 0,
                'title': 'Date'
            },
            {
                'targets': 1,
                'title': 'Title(english)'
            },
            {
                'targets': 2,
                'title': 'Title(native)'
            },
            {
                'targets': 3,
                'title': 'Sent to'
            },
            {
                'targets': 4,
                'title': 'Link',
                'render': (data, type, row, meta) => '<a href="' + data + '"><span class="fa fa-3x fa-external-link"></span></a>',
                'orderable': false
            },
        ]
    });
});