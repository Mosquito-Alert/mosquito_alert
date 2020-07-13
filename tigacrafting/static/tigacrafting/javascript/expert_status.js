$(document).ready(function() {



});

function getPendingReports(user, group){
    var flag = $('#current_status_collapse_pending'+user+'_'+group).hasClass("collapse in");

    if(!flag){
        var url = '/experts/status/reports/pending';
        url = url + '?u=' + user
        var urlReport = _expert_report_status;
        $('#loading_'+user+'_'+group+'_pending').addClass('asyncload-big');

        $('#current_status_collapse_pending_'+user+'_'+group).hide();

        $.ajax({
            url: url,
            method: "GET",
            success: function( data, textStatus, jqXHR ) {
                $('#loading_'+user+'_'+group+'_pending').removeClass('asyncload-big');

                $('#current_status_collapse_pending_'+user+'_'+group).show();
                var dataSize = Object.values(data.pendingReports).length;
                var filas = [];
                var datos = [];
                for(i=0;i<dataSize; i++){
                    datos[i] = {
                            "report_id": '<a href='+ urlReport +'?version_uuid='+ data.pendingReports[i].report_id +'>'+ data.pendingReports[i].report_id +'</a>',
                            "givenToExpert": data.pendingReports[i].givenToExpert,
                            "lastMod": data.pendingReports[i].lastModified,
                            "draftStatus": data.pendingReports[i].draftStatus + ' ' + data.pendingReports[i].getScore + ' ' + data.pendingReports[i].getCategory
                    }
                }

                $('#current_status_collapse_pending_'+user+'_'+group).DataTable({
                        data: datos,
                        columns: [
                            {data: 'report_id'},
                            {data: 'givenToExpert'},
                            {data: 'lastMod'},
                            {data: 'draftStatus'},
                        ],
                        searching: false,
                        ordering: false,
                        destroy: true
                });
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(errorThrown);
            }
        });
    }else{
        $('#current_status_collapse_pending_'+user+'_'+group).DataTable().clear().draw();


    }
};

function getCompleteReports(user, group){
    var flag = $('#current_status_collapse_complete'+user+'_'+group).hasClass("collapse in");
    if(!flag){
        var url = '/experts/status/reports/complete';
        url = url + '?u=' + user
        var urlReport = _expert_report_status;

        $('#loading_'+user+'_'+group+'_complete').addClass("asyncload-big");

        $('#current_status_collapse_complete'+user+'_'+group).hide();

        $.ajax({
            url: url,
            method: "GET",
            success: function( data, textStatus, jqXHR ) {
                $('#current_status_collapse_complete'+user+'_'+group).show();
                $('#loading_'+user+'_'+group+'_complete').removeClass("asyncload-big");
                var dataSize = Object.values(data.completeReports).length;
                var filas = [];
                var datos = [];
                for(i=0;i<dataSize; i++){
                   datos[i] = {
                        "report_id": '<a href='+ urlReport +'?version_uuid='+ data.completeReports[i].report_id +'>'+ data.completeReports[i].report_id +'</a>',
                        "givenToExpert": data.completeReports[i].givenToExpert,
                        "lastMod": data.completeReports[i].lastModified,
                        "draftStatus": data.completeReports[i].draftStatus + ' ' + data.completeReports[i].getScore + ' ' + data.completeReports[i].getCategory
                    }
                }

                $('#current_status_collapse_complete_'+user+'_'+group).DataTable({
                    data: datos,
                    columns: [
                        {data: 'report_id'},
                        {data: 'givenToExpert'},
                        {data: 'lastMod'},
                        {data: 'draftStatus'},
                    ],
                    searching: false,
                    ordering: false,
                    destroy: true
                });
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log(errorThrown);
            }
        });
    }else{
        var table = $('#current_status_collapse_complete_'+user+'_'+group).DataTable();
        table.clear();
    }
};