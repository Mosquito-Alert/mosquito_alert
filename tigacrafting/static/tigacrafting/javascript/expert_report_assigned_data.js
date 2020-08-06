$(document).ready(function() {
    console.log(data);
    $('#expertsAssigned').DataTable({
        paging: false,
        data: data,
        columns: [
            {data: 'codiReport'},
            {data: 'ubication'},
            {data: 'assignationDate'},
            {data: 'assignedExpert'},

        ],
        "order": [[ 2, "desc" ]]
    });

});
